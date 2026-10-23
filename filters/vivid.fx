// Сочно: «умная» насыщенность (бледные цвета сильнее, яркие почти не трогаются) и контраст.
#include "SoberStrap.fxh"
uniform float VividStrength = 1.0;

float4 PS_Vivid(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float3 c = tex2D(SS_BackBuffer, uv).rgb;
    float mx = max(c.r, max(c.g, c.b));
    float mn = min(c.r, min(c.g, c.b));
    float sat = mx - mn;
    float3 v = SS_Saturate(c, 1.0 + 0.6 * VividStrength * (1.0 - sat));
    v = lerp(v, v * v * (3.0 - 2.0 * v), 0.25 * VividStrength);
    return float4(saturate(v), 1.0);
}
technique Vivid { pass { VertexShader = SS_VS; PixelShader = PS_Vivid; } }
