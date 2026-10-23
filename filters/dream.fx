// Мечта: мягкое свечение вокруг ярких мест и чуть пастельные цвета.
#include "SoberStrap.fxh"
uniform float DreamStrength = 1.0;

float4 PS_Dream(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float3 c = tex2D(SS_BackBuffer, uv).rgb;
    float3 glow = 0.0;
    float total = 0.0;
    for (int ring = 1; ring <= 3; ring++)
    {
        for (int i = 0; i < 8; i++)
        {
            float a = i * 0.785398 + ring * 0.4;
            float2 o = float2(cos(a), sin(a)) * SS_PIXEL * ring * 9.0;
            float3 s = tex2D(SS_BackBuffer, uv + o).rgb;
            float w = 1.0 / ring;
            glow += max(s - 0.55, 0.0) * w;
            total += w;
        }
    }
    glow /= total;
    float3 d = c + glow * 2.2 * DreamStrength;
    d = lerp(d, SS_Saturate(d, 0.85) + 0.03, 0.5 * DreamStrength);
    return float4(saturate(d), 1.0);
}
technique Dream { pass { VertexShader = SS_VS; PixelShader = PS_Dream; } }
