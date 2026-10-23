// Общее для фильтров SoberStrap: кадр игры и вершинный шейдер на весь экран.
#pragma once

texture2D SS_BackBufferTex : COLOR;
sampler2D SS_BackBuffer { Texture = SS_BackBufferTex; };
sampler2D SS_BackBufferPoint { Texture = SS_BackBufferTex; MinFilter = POINT; MagFilter = POINT; };

uniform float SS_Timer < source = "timer"; >;

#define SS_PIXEL float2(BUFFER_RCP_WIDTH, BUFFER_RCP_HEIGHT)

void SS_VS(in uint id : SV_VertexID, out float4 pos : SV_Position, out float2 uv : TEXCOORD)
{
    uv.x = (id == 2) ? 2.0 : 0.0;
    uv.y = (id == 1) ? 2.0 : 0.0;
    pos = float4(uv * float2(2.0, -2.0) + float2(-1.0, 1.0), 0.0, 1.0);
}

float SS_Luma(float3 c) { return dot(c, float3(0.2126, 0.7152, 0.0722)); }

float SS_Hash(float2 p)
{
    return frac(sin(dot(p, float2(12.9898, 78.233))) * 43758.5453);
}

float SS_Vignette(float2 uv, float amount)
{
    float2 d = uv - 0.5;
    return 1.0 - amount * smoothstep(0.25, 0.85, dot(d, d) * 2.2);
}

float3 SS_Saturate(float3 c, float s) { return lerp(SS_Luma(c).xxx, c, s); }
