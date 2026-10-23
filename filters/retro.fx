// Ретро-телевизор: строки развёртки, разъезд цветов, маска кинескопа, шум.
#include "SoberStrap.fxh"
uniform float RetroStrength = 1.0;

float4 PS_Retro(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float3 src = tex2D(SS_BackBuffer, uv).rgb;
    float2 d = uv - 0.5;
    float2 shift = d * 0.004;
    float3 c;
    c.r = tex2D(SS_BackBuffer, uv + shift).r;
    c.g = src.g;
    c.b = tex2D(SS_BackBuffer, uv - shift).b;
    float line = 0.82 + 0.18 * sin(pos.y * 3.14159);
    int col = int(pos.x) % 3;
    float3 mask = col == 0 ? float3(1.0, 0.88, 0.88) : (col == 1 ? float3(0.88, 1.0, 0.88) : float3(0.88, 0.88, 1.0));
    c *= line * mask * 1.12;
    c += (SS_Hash(float2(pos.y, frac(SS_Timer * 0.0007)) * 0.01) - 0.5) * 0.05;
    c *= SS_Vignette(uv, 0.6);
    return float4(lerp(src, saturate(c), RetroStrength), 1.0);
}
technique Retro { pass { VertexShader = SS_VS; PixelShader = PS_Retro; } }
