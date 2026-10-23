// Пиксель-арт: крупные пиксели и ограниченная палитра, как в старых приставках.
#include "SoberStrap.fxh"
uniform float PixelSize = 4.0;
uniform float PixelColors = 8.0;

float4 PS_Pixel(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float2 cells = float2(BUFFER_WIDTH, BUFFER_HEIGHT) / PixelSize;
    float2 q = (floor(uv * cells) + 0.5) / cells;
    float3 c = tex2D(SS_BackBufferPoint, q).rgb;
    // лёгкий дизеринг, чтобы градиенты не превращались в полосы
    float2 b = floor(fmod(floor(uv * cells), 2.0));
    float d = ((b.x * 2.0 + b.y) / 4.0 - 0.375) * 0.6 / PixelColors;
    c = floor(saturate(c + d) * PixelColors + 0.5) / PixelColors;
    return float4(c, 1.0);
}
technique Pixel { pass { VertexShader = SS_VS; PixelShader = PS_Pixel; } }
