/**
 * @file reduce_custom.cpp
 *
 * Copyright (C) 2022-2024. Huawei Technologies Co., Ltd. All rights reserved.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 */
#include "kernel_operator.h"
#define REDUCE_TILING_0 1
#define REDUCE_TILING_1 2
#define REDUCE_TILING_2 3

class KernelReduce {
static constexpr uint32_t DEFAULT_BLK_STRIDE = 1;
static constexpr uint32_t DEFAULT_REP_STRIDE = 8;
static constexpr uint32_t REP_LEN = 256;
static constexpr uint32_t BLK_LEN = 32;
public:
    __aicore__ inline KernelReduce() {}
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR z, uint32_t totalLength, uint32_t outLength)
    {
        this->totalLength = totalLength;
        this->outLength = outLength;

        xGm.SetGlobalBuffer((__gm__ DTYPE_X *)x, totalLength);
        zGm.SetGlobalBuffer((__gm__ DTYPE_Z *)z, outLength);
        pipe.InitBuffer(inQueueX, 1, totalLength * sizeof(DTYPE_X));
        pipe.InitBuffer(outQueueZ, 1, outLength * sizeof(DTYPE_Z));
    }
    __aicore__ inline void Process1()
    {
        CopyIn();
        Compute1();
        CopyOut();
    }
    __aicore__ inline void Process2()
    {
        CopyIn();
        Compute2();
        CopyOut();
    }
    __aicore__ inline void Process3()
    {
        CopyIn();
        Compute3();
        CopyOut();
    }

private:
    __aicore__ inline void CopyIn()
    {
        AscendC::LocalTensor<DTYPE_X> xLocal = inQueueX.AllocTensor<DTYPE_X>();
        AscendC::DataCopy(xLocal, xGm, totalLength);
        inQueueX.EnQue(xLocal);
    }
    // Only WholeReduceSum is used under 256B.
    __aicore__ inline void Compute1()
    {
        AscendC::LocalTensor<DTYPE_X> xLocal = inQueueX.DeQue<DTYPE_X>();
        AscendC::LocalTensor<DTYPE_Z> zLocal = outQueueZ.AllocTensor<DTYPE_Z>();
        constexpr int64_t maskLen = REP_LEN / sizeof(DTYPE_X);
        AscendC::WholeReduceSum<DTYPE_X>(zLocal, xLocal, maskLen, 1,
            DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULT_REP_STRIDE);
        outQueueZ.EnQue<DTYPE_Z>(zLocal);
        inQueueX.FreeTensor(xLocal);
    }
    // One WholeReduceSum and one BlockReduceSum are used in (256B,2KB](for float input) and (256B,4KB](for half input).
    __aicore__ inline void Compute2()
    {
        AscendC::LocalTensor<DTYPE_X> xLocal = inQueueX.DeQue<DTYPE_X>();
        AscendC::LocalTensor<DTYPE_Z> zLocal = outQueueZ.AllocTensor<DTYPE_Z>();
        pipe.InitBuffer(calcBuf, totalLength * sizeof(DTYPE_X));
        AscendC::LocalTensor<DTYPE_X> tempTensor1 = calcBuf.Get<DTYPE_X>();
        constexpr uint32_t c0Count = BLK_LEN / sizeof(DTYPE_X);
        const uint32_t blockNum0 = (totalLength + c0Count - 1) / c0Count;
        AscendC::SetMaskCount();
        AscendC::SetVectorMask<DTYPE_X>(0, totalLength);
        AscendC::BlockReduceSum<DTYPE_X, false>(tempTensor1, xLocal, AscendC::MASK_PLACEHOLDER, 1,
            DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULT_REP_STRIDE);
        AscendC::PipeBarrier<PIPE_V>();
        AscendC::SetVectorMask<DTYPE_X>(0, blockNum0);
        AscendC::WholeReduceSum<DTYPE_X, false>(zLocal, tempTensor1, AscendC::MASK_PLACEHOLDER, 1,
            DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULT_REP_STRIDE);
        AscendC::PipeBarrier<PIPE_V>();
        AscendC::SetMaskNorm();
        outQueueZ.EnQue<DTYPE_Z>(zLocal);
        inQueueX.FreeTensor(xLocal);
    }
    // Two WholeReduceSum are used in (2KB,16KB](for float input) and (4KB,32KB](for half input).
    __aicore__ inline void Compute3()
    {
        AscendC::LocalTensor<DTYPE_X> xLocal = inQueueX.DeQue<DTYPE_X>();
        AscendC::LocalTensor<DTYPE_Z> zLocal = outQueueZ.AllocTensor<DTYPE_Z>();
        pipe.InitBuffer(calcBuf, totalLength * sizeof(DTYPE_X));
        AscendC::LocalTensor<DTYPE_X> tempTensor1 = calcBuf.Get<DTYPE_X>();
        const uint32_t repeatNum = (totalLength * sizeof(DTYPE_X) + REP_LEN - 1) / REP_LEN;
        AscendC::SetMaskCount();
        AscendC::SetVectorMask<DTYPE_X>(0, totalLength);
        AscendC::WholeReduceSum<DTYPE_X, false>(tempTensor1, xLocal, AscendC::MASK_PLACEHOLDER, 1,
            DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULT_REP_STRIDE);
        AscendC::PipeBarrier<PIPE_V>();
        AscendC::SetVectorMask<DTYPE_X>(0, repeatNum);
        AscendC::WholeReduceSum<DTYPE_X, false>(zLocal, tempTensor1, AscendC::MASK_PLACEHOLDER, 1,
            DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULT_REP_STRIDE);
        AscendC::PipeBarrier<PIPE_V>();
        AscendC::SetMaskNorm();
        outQueueZ.EnQue<DTYPE_Z>(zLocal);
        inQueueX.FreeTensor(xLocal);
    }
    __aicore__ inline void CopyOut()
    {
        AscendC::LocalTensor<DTYPE_Z> zLocal = outQueueZ.DeQue<DTYPE_Z>();
        AscendC::DataCopy(zGm, zLocal, this->outLength);
        outQueueZ.FreeTensor(zLocal);
    }

private:
    AscendC::TPipe pipe;
    AscendC::TQue<AscendC::TPosition::VECIN, 1> inQueueX;
    AscendC::TQue<AscendC::TPosition::VECOUT, 1> outQueueZ;
    AscendC::TBuf<AscendC::TPosition::VECCALC> calcBuf;
    AscendC::GlobalTensor<DTYPE_X> xGm;
    AscendC::GlobalTensor<DTYPE_Z> zGm;
    uint32_t totalLength;
    uint32_t outLength;
};

extern "C" __global__ __aicore__ void reduce_custom(GM_ADDR x, GM_ADDR z, GM_ADDR workspace, GM_ADDR tiling)
{
    GET_TILING_DATA(tiling_data, tiling);
    KernelReduce op;
    op.Init(x, z, tiling_data.totalLength, tiling_data.outLength);
    if (TILING_KEY_IS(REDUCE_TILING_0)) {
        op.Process1();
    } else if (TILING_KEY_IS(REDUCE_TILING_1)) {
        op.Process2();
    } else if (TILING_KEY_IS(REDUCE_TILING_2)) {
        op.Process3();
    }
}

#ifndef ASCENDC_CPU_DEBUG
// call of kernel function
void reduce_custom_do(uint32_t blockDim, void *l2ctrl, void *stream, uint8_t *x, uint8_t *z,
                   uint8_t *workspace, uint8_t *tiling)
{
    reduce_custom<<<blockDim, l2ctrl, stream>>>(x, z, workspace, tiling);
}
#endif