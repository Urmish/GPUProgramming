#include <stdio.h>

#define BLOCK_SIZE 2
int get_max_size (int a, int d)
{
    int temp = a/d;
    if (a%d != 0)
    {
        temp = temp+1;
    }
    return temp;
}

#define gpuErrchk(ans) { gpuAssert((ans), __FILE__, __LINE__); }
inline void gpuAssert(cudaError_t code, const char *file, int line, bool abort=true)
{
   if (code != cudaSuccess) 
   {
      fprintf(stderr,"GPUassert: %s %s %d\n", cudaGetErrorString(code), file, line);
      if (abort) exit(code);
   }
}

__global__ void fixup(unsigned int *input, unsigned int *aux, int len) {
    unsigned int t = threadIdx.x, start = 2 * blockIdx.x * BLOCK_SIZE;
    if (blockIdx.x > 0) {
       if (start + t < len)
          input[start + t] += aux[blockIdx.x ];
       if (start + BLOCK_SIZE + t < len)
          input[start + BLOCK_SIZE + t] += aux[blockIdx.x ];
    }
}

__global__ void scanPart1 (unsigned int* input,
			   unsigned int* output,
			   unsigned int* aux,
			   int numElems)
{
	extern __shared__ unsigned int sdata[];
	//int myGlobalId = blockDim.x*blockIdx.x + threadIdx.x;
	int myLocalId = threadIdx.x;
	int start = 2 * blockIdx.x * BLOCK_SIZE; //Each block reads 2*BLOCK_SIZE so idx*this value is total inputs read
	int lastReadValue = 0;
	//Input Read
	if (start + myLocalId < numElems)
	{
       		sdata[myLocalId] = input[start + myLocalId];
	}
	else
	{
       		sdata[myLocalId] = 0;
	}
	if (start + BLOCK_SIZE + myLocalId  < numElems)
	{
       		sdata[BLOCK_SIZE + myLocalId] = input[start + BLOCK_SIZE + myLocalId];
	}
    	else
	{
       		sdata[BLOCK_SIZE + myLocalId] = 0;
	}
	__syncthreads();
	lastReadValue = sdata[2*BLOCK_SIZE-1];
	
	//Reduction
	int stride;
	for (stride = 1; stride <= BLOCK_SIZE; stride <<= 1) 
	{
       		int index = (myLocalId + 1) * stride * 2 - 1;
	        if (index < 2 * BLOCK_SIZE)
 	        	sdata[index] += sdata[index - stride];
	        __syncthreads();
	}
	if (myLocalId == 0)
	{
		sdata[2*BLOCK_SIZE-1] = 0;
	}
	__syncthreads();
	// Post reduction
	for (stride = BLOCK_SIZE ; stride; stride >>= 1) 
	{
       		int index = (myLocalId + 1) * stride * 2 - 1;
	        //if (index + stride < 2 * BLOCK_SIZE)
	        if (index < 2 * BLOCK_SIZE)
		{
//			unsigned int temp = sdata[index+stride];
//         		sdata[index + stride] += sdata[index];
//			sdata[index] = temp;
			unsigned int temp = sdata[index];
         		sdata[index] += sdata[index-stride];
			sdata[index-stride] = temp;
		}
	        __syncthreads();
    	}

	if (start + myLocalId < numElems)
	       	output[start + myLocalId] = sdata[myLocalId];
	if (start + BLOCK_SIZE + myLocalId < numElems)
        	output[start + BLOCK_SIZE + myLocalId] = sdata[BLOCK_SIZE + myLocalId];

	if (myLocalId == 0 && aux!=NULL)
       		aux[blockIdx.x] = sdata[2 * BLOCK_SIZE - 1] + lastReadValue;
}

__global__ void splitInput(int compareAndValue,
			   unsigned int* input,
			   unsigned int* output,
			   int maxElements)
{
	int myGlobalId = blockDim.x*blockIdx.x + threadIdx.x;
	if (myGlobalId >= maxElements)
	{
		return;
	}
	if(((input[myGlobalId] & compareAndValue)) > 0)
	{
		printf("%d. %d & %d is 0\n",myGlobalId,input[myGlobalId],compareAndValue);
		output[myGlobalId] = 0;
	}
	else
	{
		printf("%d. %d & %d is 1\n",myGlobalId,input[myGlobalId],compareAndValue);
		output[myGlobalId] = 1;
	}
	printf("%d. %d\n",myGlobalId,input[myGlobalId]);
}

__global__ void possibleLocations (unsigned int* input,
				   unsigned int* input_scan,
				   unsigned int* output,
				   unsigned int numElems,
				   unsigned int compareAndValue)
{
	int myGlobalId = blockDim.x*blockIdx.x + threadIdx.x;
	int myLocalId = threadIdx.x;
	int start = 2 * blockIdx.x * BLOCK_SIZE; //Each block reads 2*BLOCK_SIZE so idx*this value is total inputs read
	int total = input_scan[numElems-1] + (((input[numElems-1] & compareAndValue) > 0)?0:1);
	printf("Total %d\n",total);
	if (myLocalId + start < numElems)
	{
		//output[myGlobalId] = myGlobalId - input_scan[myGlobalId] + total;
		output[start + myLocalId] = start + myLocalId  - input_scan[start + myLocalId] + total;
		printf("%d. %d might go to %d\n",start + myLocalId,input[myLocalId + start], output[start + myLocalId]);
	}
	if (myLocalId + start + BLOCK_SIZE < numElems)
	{
		output[start + myLocalId + BLOCK_SIZE] = start + myLocalId + BLOCK_SIZE - input_scan[start + myLocalId + BLOCK_SIZE] + total ;
		printf("%d. %d might go to %d\n",start + myLocalId,input[myLocalId + start+BLOCK_SIZE], output[start + myLocalId + BLOCK_SIZE]);
	}
	
}


__global__ void finalLocations (   unsigned int* input,
				   unsigned int* input_scan,
				   unsigned int* input_vals,
				   unsigned int* d_setOneIfOne,
				   unsigned int* output,
				   unsigned int numElems)
{
	int myGlobalId = blockDim.x*blockIdx.x + threadIdx.x;
	int myLocalId = threadIdx.x;
	int start = 2 * blockIdx.x * BLOCK_SIZE; //Each block reads 2*BLOCK_SIZE so idx*this value is total inputs read
	if (myLocalId + start < numElems)
	{
		if (d_setOneIfOne[myLocalId + start] == 0)
		{
			output[input[myLocalId + start]] = input_vals[myLocalId + start];
			printf("%d. %d goes to %d\n",myGlobalId, input_vals[myLocalId + start], input[myLocalId + start]);
		}	
		else
		{
			output[input_scan[myLocalId + start]] = input_vals[myLocalId + start];
			printf("%d. %d goes to %d\n",myGlobalId, input_vals[myLocalId + start], input_scan[myLocalId + start]);
		}
	}
	if (myLocalId + start + BLOCK_SIZE < numElems)
	{	
		if (d_setOneIfOne[myLocalId + start + BLOCK_SIZE] == 0)
		{
			output[input[myLocalId + start + BLOCK_SIZE]] = input_vals[myLocalId + start + BLOCK_SIZE];
			printf("%d. %d goes to %d\n",myGlobalId, input_vals[myLocalId + start+ BLOCK_SIZE], input[myLocalId + start +BLOCK_SIZE]);
		}	
		else
		{
			output[input_scan[myLocalId + start + BLOCK_SIZE]] = input_vals[myLocalId + start + BLOCK_SIZE];
			printf("%d. %d goes to %d\n", myGlobalId, input_vals[myLocalId + start+BLOCK_SIZE] , input_scan[myLocalId + start +BLOCK_SIZE]);
		}
	}
}

int main()
{
	unsigned int h_inputVals[10] = {3, 4, 1, 2, 7, 6, 5, 0, 9, 8};
  	unsigned int numElems = 10;
        unsigned int  h_bins[2];
	int histo_size = sizeof(unsigned int)*2;
	unsigned int* d_inputVals;
	gpuErrchk(cudaMalloc(&d_inputVals, numElems*sizeof(numElems)));
	gpuErrchk(cudaMemcpy(d_inputVals, h_inputVals, numElems*sizeof(numElems), cudaMemcpyHostToDevice));
        unsigned int* d_bins;
        gpuErrchk(cudaMalloc(&d_bins, histo_size));
     	unsigned int* d_setOneIfOne;
     	unsigned int* d_possibleLocations;
     	unsigned int* d_finalLocations;
     	unsigned int* d_scan;
     	unsigned int* h_scan;
	h_scan = (unsigned int*)malloc(numElems*sizeof(numElems));
	gpuErrchk(cudaMalloc(&d_setOneIfOne, numElems*sizeof(numElems)));
	gpuErrchk(cudaMalloc(&d_scan, numElems*sizeof(numElems)));
	gpuErrchk(cudaMalloc(&d_possibleLocations, numElems*sizeof(numElems)));
	for (int i=0;i<10;i++)
	{
	       printf("%d ", h_inputVals[i]);
	}
	printf("\n");
 
     	unsigned int* h_setOneIfOne;
	h_setOneIfOne = (unsigned int*)malloc(numElems*sizeof(numElems));
        for (int i=0;i<4;i++)
        {
		 gpuErrchk(cudaMalloc(&d_finalLocations, numElems*sizeof(numElems)));
		 printf("Round %d\n",i);
 	       	 gpuErrchk(cudaMemset(d_bins, 0, histo_size));
 	       	 gpuErrchk(cudaMemset(d_setOneIfOne,0, numElems*sizeof(numElems)));
 	       	 gpuErrchk(cudaMemset(d_scan,0, numElems*sizeof(numElems)));
	         int compareAndValue = 1 << i;
		 int numberThreadPerBlock = 512;
		 dim3 blockDim_si(numberThreadPerBlock);
		 dim3 gridDim_si(get_max_size(numElems,numberThreadPerBlock));
		 splitInput<<<gridDim_si,blockDim_si>>>(compareAndValue, d_inputVals, d_setOneIfOne, numElems);
	         gpuErrchk(cudaMemcpy(h_setOneIfOne, d_setOneIfOne, numElems*sizeof(numElems), cudaMemcpyDeviceToHost));
		 for (int i=0;i<10;i++)
		 {
			printf("%d ", h_setOneIfOne[i]);
			h_setOneIfOne[i] = 0;
		 }
		 printf("\n");
		 dim3 blockDim_sp(BLOCK_SIZE);
		 dim3 gridDim_sp(get_max_size(numElems,2*BLOCK_SIZE));
     		 unsigned int* d_aux;
     		 unsigned int* d_aux_scan;
		 unsigned int* h_aux;
	 	 gpuErrchk(cudaMalloc(&d_aux, get_max_size(numElems,2*BLOCK_SIZE)*sizeof(unsigned int)));
	 	 gpuErrchk(cudaMalloc(&d_aux_scan, get_max_size(numElems,2*BLOCK_SIZE)*sizeof(unsigned int)));
		 h_aux = (unsigned int*)malloc(get_max_size(numElems,2*BLOCK_SIZE)*sizeof(unsigned int));
		 
	//         gpuErrchk(cudaMemcpy(d_scan, d_setOneIfOne, numElems*sizeof(numElems), cudaMemcpyDeviceToDevice));
		 printf ("Size of Kernel is Grid - %d, Block - %d\n",gridDim_sp.x,blockDim_sp.x);
		 scanPart1<<<gridDim_sp,blockDim_sp,BLOCK_SIZE*2*sizeof(unsigned int)>>> (d_setOneIfOne,d_scan,d_aux,numElems);	
	         gpuErrchk(cudaMemcpy(h_scan, d_scan, numElems*sizeof(numElems), cudaMemcpyDeviceToHost));	
		 for (int i=0;i<10;i++)
		 {
			printf("%d ", h_scan[i]);
			h_scan[i] = 0;
		 }
		 printf("\n");
		 dim3 blockDim_sp2(get_max_size(numElems,2*BLOCK_SIZE));
	         gpuErrchk(cudaMemcpy(h_aux, d_aux, blockDim_sp2.x*sizeof(unsigned int), cudaMemcpyDeviceToHost));	
		 for (int i=0;i<blockDim_sp2.x;i++)
		 {
			printf("%d ", h_aux[i]);
			h_aux[i] = 0;
		 }
		 printf("\n");

		 printf ("Size of Kernel is Grid - 1, Block - %d\n",blockDim_sp2.x);
		 scanPart1<<<1,blockDim_sp2,BLOCK_SIZE*2*sizeof(unsigned int)>>>(d_aux,d_aux_scan,NULL,blockDim_sp2.x);	
	         gpuErrchk(cudaMemcpy(h_aux, d_aux_scan, blockDim_sp2.x*sizeof(unsigned int), cudaMemcpyDeviceToHost));	
		 for (int i=0;i<blockDim_sp2.x;i++)
		 {
			printf("%d ", h_aux[i]);
			h_aux[i] = 0;
		 }
		 printf("\n");
		 printf ("Size of Kernel is Grid - %d, Block - %d\n",gridDim_sp.x,blockDim_sp.x);
		 fixup<<<gridDim_sp,blockDim_sp>>>(d_scan,d_aux_scan,numElems);
	         gpuErrchk(cudaMemcpy(h_scan, d_scan, numElems*sizeof(numElems), cudaMemcpyDeviceToHost));	
		 for (int i=0;i<10;i++)
		 {
			printf("%d ", h_scan[i]);
			h_scan[i] = 0;
		 }
		 printf("\n");
		 printf ("Size of Kernel is Grid - %d, Block - %d\n",gridDim_sp.x,blockDim_sp.x);
		 possibleLocations<<<gridDim_sp,blockDim_sp>>>(d_inputVals,d_scan, d_possibleLocations, numElems, compareAndValue);
                 gpuErrchk(cudaMemcpy(h_setOneIfOne, d_possibleLocations, numElems*sizeof(numElems), cudaMemcpyDeviceToHost));
		 printf ("Possible Locations are \n");
		 for (int i=0;i<10;i++)
		 {
			printf("%d ", h_setOneIfOne[i]);
			h_setOneIfOne[i] = 0;
		 }
		 printf ("\n");
		 finalLocations<<<gridDim_sp,blockDim_sp>>>(d_possibleLocations,d_scan,d_inputVals, d_setOneIfOne, d_finalLocations,numElems);
	 	 cudaDeviceSynchronize(); 
		 gpuErrchk(cudaFree(d_inputVals));
		 d_inputVals = d_finalLocations; 
                 gpuErrchk(cudaMemcpy(h_setOneIfOne, d_finalLocations, numElems*sizeof(numElems), cudaMemcpyDeviceToHost));
		 printf ("\nFinal Positions are \n");
		 for (int i=0;i<10;i++)
		 {
		        printf("%d ", h_setOneIfOne[i]);
		        h_setOneIfOne[i] = 0;
		 }

		 printf("\n******************************************\n");
	         //printf("Histogram Values - %d %d %d %d %d \n", h_bins[0], h_bins[1], h_bins[0]+h_bins[1], numElems, compareAndValue);
        }
        gpuErrchk(cudaFree(d_bins));
	gpuErrchk(cudaFree(d_setOneIfOne));
	free(h_setOneIfOne);
	gpuErrchk(cudaFree(d_possibleLocations));
	free(h_scan);
	return 0;
}

