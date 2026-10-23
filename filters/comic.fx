// Комикс: точечный растр в тенях, чёрные контуры и яркие цвета.
#include "SoberStrap.fxh"
uniform float ComicStrength = 1.0;

float4 PS_Comic(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
    float3 src = tex2D(SS_BackBuffer, uv).rgb;
    float2 p = SS_PIXEL * 1.5;
    float gx = SS_Luma(tex2D(SS_BackBuffer, uv + float2(p.x, 0)).rgb) - SS_Luma(tex2D(SS_BackBuffer, uv - float2(p.x, 0)).rgb);
    float gy = SS_Luma(tex2D(SS_BackBuffer, uv + float2(0, p.y)).rgb) - SS_Luma(tex2D(SS_BackBuffer, uv - float2(0, p.y)).rgb);
    float edge = smoothstep(0.12, 0.3, sqrt(gx * gx + gy * gy));
    float l = SS_Luma(src);
    // растр: сетка точек под 45°, радиус точки растёт в тенях
    float2 g = float2(pos.x + pos.y, pos.x - pos.y) * 0.7071 / 7.0;
    float dist = length(frac(g) - 0.5);
    float dots = step(dist, (1.0 - l) * 0.55);
    float3 c = SS_Saturate(src, 1.3);
    c = floor(c * 7.0 + 0.5) / 7.0;
    c *= 1.0 - dots * 0.22;
    c = lerp(c, 0.0, edge);
    return float4(lerp(src, saturate(c), ComicStrength), 1.0);
}
technique Comic { pass { VertexShader = SS_VS; PixelShader = PS_Comic; } }
