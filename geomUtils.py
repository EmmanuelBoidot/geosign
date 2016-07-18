import random

# A function to randomly select k items from stream[0..n-1].
def selectKItems(numPoints, numPointsToSample):
  # reservoir[] is the output array. Initialize it with
  # first k elements from stream[]
  reservoir = range(numPointsToSample)

  # Iterate from the (k+1)th element to nth element
  for i in range(numPointsToSample,numPoints):
    # Pick a random index from 0 to i.
    j = random.randrange(i+1);

    # If the randomly  picked index is smaller than k, then replace
    # the element present at the index with new element from stream
    if (j < numPointsToSample):
      reservoir[j] = i

  return sorted(reservoir)