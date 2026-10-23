// Мультик: плоские цвета и тёмные контуры по краям предметов.
#include "SoberStrap.fxh"
uniform float ToonLevels = 7.0;
uniform float ToonOutline = 1.0;

float4 PS_Toon(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float3 c = tex2D(SS_BackBuffer, uv).rgb;
    float2 p = SS_PIXEL * 1.5;
    float tl = SS_Luma(tex2D(SS_BackBuffer, uv + p * float2(-1, -1)).rgb);
    float t  = SS_Luma(tex2D(SS_BackBuffer, uv + p * float2( 0, -1)).rgb);
    float tr = SS_Luma(tex2D(SS_BackBuffer, uv + p * float2( 1, -1)).rgb);
    float l  = SS_Luma(tex2D(SS_BackBuffer, uv + p * float2(-1,  0)).rgb);
    float r  = SS_Luma(tex2D(SS_BackBuffer, uv + p * float2( 1,  0)).rgb);
    float bl = SS_Luma(tex2D(SS_BackBuffer, uv + p * float2(-1,  1)).rgb);
    float b  = SS_Luma(tex2D(SS_BackBuffer, uv + p * float2( 0,  1)).rgb);
    float br = SS_Luma(tex2D(SS_BackBuffer, uv + p * float2( 1,  1)).rgb);
    float gx = -tl - 2.0 * l - bl + tr + 2.0 * r + br;
    float gy = -tl - 2.0 * t - tr + bl + 2.0 * b + br;
    float edge = smoothstep(0.18, 0.45, sqrt(gx * gx + gy * gy));
    // постеризация по яркости — оттенок сохраняется
    float lum = SS_Luma(c) + 0.0001;
    float q = floor(lum * ToonLevels + 0.5) / ToonLevels;
    float3 flat = SS_Saturate(lerp(c, c * (q / lum), 0.8), 1.2);
    flat = lerp(flat, float3(0.05, 0.05, 0.08), edge * ToonOutline);
    return float4(saturate(flat), 1.0);
}
technique Toon { pass { VertexShader = SS_VS; PixelShader = PS_Toon; } }
