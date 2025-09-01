#include <stdint.h>
#include <stdlib.h>



#define YY 118
#define XX 118
#define SIZE 119

void search_img(uint8_t image[SIZE+1][SIZE+1][3], uint8_t basemap[SIZE][SIZE],
                int start_x, int start_y)
{
    int max_size = SIZE * SIZE;
    int *q_x = (int*)malloc(max_size * sizeof(int));
    int *q_y = (int*)malloc(max_size * sizeof(int));
    int head = 0, tail = 0;

    uint8_t index_bm[YY+1][XX+1];

    for(int y = 0; y < YY+1; y++) {
        for(int x = 0; x < XX+1; x++) {
            basemap[y][x] = 1;
            index_bm[y][x] = 1;
        }
    }

    if (start_x < 0 || start_x > XX || start_y < 0 || start_y > YY) {
        free(q_x); free(q_y);
        return;
    }

    q_x[tail] = start_x;
    q_y[tail] = start_y;
    tail++;
    index_bm[start_y][start_x] = 0;

    int directions[4][2] = {{0,-1},{0,1},{-1,0},{1,0}};

    while(head < tail){
        int a_x = q_x[head];
        int a_y = q_y[head];
        head++;

        uint8_t val = image[a_y][a_x][0];

        if(val < 128){
            if(basemap[a_y][a_x] == 1)
                basemap[a_y][a_x] = 0;

            for(int d = 0; d < 4; d++){
                int nx = a_x + directions[d][0];
                int ny = a_y + directions[d][1];
                if(nx >= 0 && nx <= XX && ny >= 0 && ny <= YY && index_bm[ny][nx] == 1){
                    index_bm[ny][nx] = 0;
                    q_x[tail] = nx;
                    q_y[tail] = ny;
                    tail++;
                }
            }
        } else {
            basemap[a_y][a_x] = 2;
        }
    }

    free(q_x);
    free(q_y);
}
