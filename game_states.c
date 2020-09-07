#include "gamestates.h"

#define NCATS 13
#define UPPER_THRESHOLD 64
#define NSTATES 524288 /* 2^NCATS * UPPER_THRESHOLD */

#define CAT_MASK(state, cat) ((state) >> (cat))
#define UPPERSCORE(state) ((state) >> NCATS)

float *init_values()
{
  values = malloc(sizeof(float) * NSTATES);
  for (int i=0; i<NSTATES; i++)
    values[i]=UNK_VALUE;
  return values;
}

void export_values(float *values, FILE *fileptr)
{
  /* to implement */
}

float *import_files(float *values, FILE *fileptr)
{
  /* to implement */
}

int state_index(int upperscore, int opencats)
{
  return upperscore << 13 | opencats;
}

