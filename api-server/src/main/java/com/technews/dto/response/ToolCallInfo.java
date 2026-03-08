package com.technews.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ToolCallInfo {

    @JsonProperty("tool_name")
    private String toolName;

    @JsonProperty("tool_input")
    private Object toolInput;

    @JsonProperty("tool_output")
    private String toolOutput;

    private Integer iteration;
}