// Кино: тёплые света, бирюзовые тени, мягкая S-кривая, виньетка и зерно.
#include "SoberStrap.fxh"
uniform float CinemaStrength = 1.0;

float4 PS_Cinema(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float3 src = tex2D(SS_BackBuffer, uv).rgb;
    float l = SS_Luma(src);
    float3 c = src;
    c = lerp(c, c * float3(0.85, 1.02, 1.12), (1.0 - l) * 0.55);   // тени — в бирюзу
    c = lerp(c, c * float3(1.12, 1.0, 0.86), l * 0.45);            // света — в тепло
    c = c * c * (3.0 - 2.0 * c) * 0.35 + c * 0.65;                  // S-кривая
    c = SS_Saturate(c, 1.08);
    c *= SS_Vignette(uv, 0.45);
    c += (SS_Hash(uv * 1000.0 + frac(SS_Timer * 0.001)) - 0.5) * 0.035;
    return float4(lerp(src, saturate(c), CinemaStrength), 1.0);
}
technique Cinema { pass { VertexShader = SS_VS; PixelShader = PS_Cinema; } }
