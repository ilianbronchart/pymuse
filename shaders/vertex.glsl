#version 330 core

// Locations correspond to the locations of the attributes in the vertex array object
layout (location = 0) in vec3 vertexPos;
layout (location = 1) in vec3 vertexColor;

// The output of this shader, consumed by the next stage in the pipeline (the fragment shader)
out vec3 fragmentColor;

void main() {
    // We use vec4 for positions so that we can use matrices to transform them
    gl_Position = vec4(vertexPos, 1.0);
    fragmentColor = vertexColor;
}