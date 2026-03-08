package com.technews.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeepSearchResponse {

    @JsonProperty("article_id")
    private String articleId;

    @JsonProperty("article_title")
    private String articleTitle;

    @JsonProperty("final_report")
    private String finalReport;

    @JsonProperty("tools_used")
    private List<ToolCallInfo> toolsUsed;

    @JsonProperty("collected_info")
    private List<CollectedInfo> collectedInfo;

    private Integer iterations;

    @JsonProperty("is_complete")
    private Boolean isComplete;

    private List<Object> errors;
}