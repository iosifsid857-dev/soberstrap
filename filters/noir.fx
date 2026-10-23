// Нуар: чёрно-белое кино с жёстким контрастом и зерном.
#include "SoberStrap.fxh"
uniform float NoirStrength = 1.0;

float4 PS_Noir(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float3 src = tex2D(SS_BackBuffer, uv).rgb;
    float l = SS_Luma(src);
    l = saturate((l - 0.5) * 1.35 + 0.5);
    l = l * l * (3.0 - 2.0 * l);
    l *= SS_Vignette(uv, 0.7);
    l += (SS_Hash(uv * 1300.0 + frac(SS_Timer * 0.001)) - 0.5) * 0.06;
    return float4(lerp(src, saturate(l).xxx, NoirStrength), 1.0);
}
technique Noir { pass { VertexShader = SS_VS; PixelShader = PS_Noir; } }
