// Хэллоуин: оранжевые света, фиолетовые тени, тёмные края.
#include "SoberStrap.fxh"
uniform float HalloweenStrength = 1.0;

float4 PS_Halloween(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float3 src = tex2D(SS_BackBuffer, uv).rgb;
    float l = SS_Luma(src);
    float3 shadow = float3(0.35, 0.18, 0.5);
    float3 light = float3(1.0, 0.62, 0.25);
    float3 tone = lerp(shadow, light, smoothstep(0.1, 0.9, l));
    float3 c = lerp(src, tone * (l * 1.4 + 0.1), 0.45);
    c *= SS_Vignette(uv, 0.85);
    return float4(lerp(src, saturate(c), HalloweenStrength), 1.0);
}
technique Halloween { pass { VertexShader = SS_VS; PixelShader = PS_Halloween; } }
