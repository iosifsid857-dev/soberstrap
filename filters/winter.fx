// Зима: холодные оттенки и иней по краям экрана.
#include "SoberStrap.fxh"
uniform float WinterStrength = 1.0;

float4 PS_Winter(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float3 src = tex2D(SS_BackBuffer, uv).rgb;
    float3 c = SS_Saturate(src, 0.8) * float3(0.92, 1.0, 1.1);
    c += float3(0.02, 0.03, 0.06);
    float2 d = uv - 0.5;
    float edge = smoothstep(0.3, 0.75, length(d * float2(1.0, 1.3)));
    float frost = edge * (0.55 + 0.45 * SS_Hash(floor(uv * float2(BUFFER_WIDTH, BUFFER_HEIGHT) / 3.0)));
    c = lerp(c, float3(0.85, 0.92, 1.0), frost * 0.55);
    return float4(lerp(src, saturate(c), WinterStrength), 1.0);
}
technique Winter { pass { VertexShader = SS_VS; PixelShader = PS_Winter; } }
