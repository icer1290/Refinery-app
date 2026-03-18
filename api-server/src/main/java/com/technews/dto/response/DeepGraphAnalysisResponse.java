package com.technews.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeepGraphAnalysisResponse {

    private UUID id;

    @JsonProperty("user_id")
    private Long userId;

    @JsonProperty("article_ids")
    private List<UUID> articleIds;

    private String report;

    @JsonProperty("visualization_data")
    private Map<String, Object> visualizationData;

    @JsonProperty("max_hops")
    private Integer maxHops;

    @JsonProperty("expansion_limit")
    private Integer expansionLimit;

    @JsonProperty("created_at")
    private LocalDateTime createdAt;
}