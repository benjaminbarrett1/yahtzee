#define UNK_VALUE -1 /* impossible value */
#define ILLEGAL_CAT -1

float *init_values();
void export_values(float *values, FILE *fileptr);
float *import_files(float *values, FILE *fileptr);
int state_index(int upperscore, int opencats);

