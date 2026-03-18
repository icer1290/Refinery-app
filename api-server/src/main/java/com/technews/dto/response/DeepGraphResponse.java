package com.technews.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeepGraphResponse {

    @JsonProperty("article_ids")
    private List<String> articleIds;

    @JsonProperty("graph_nodes")
    private List<GraphNode> graphNodes;

    @JsonProperty("graph_edges")
    private List<GraphEdge> graphEdges;

    private List<Community> communities;

    private String report;

    @JsonProperty("visualization_data")
    private VisualizationData visualizationData;

    private List<Map<String, Object>> errors;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class GraphNode {
        private String id;
        private String label;
        private String type;
        private String description;
        @JsonProperty("mention_count")
        private Integer mentionCount;
        @JsonProperty("article_count")
        private Integer articleCount;
        @JsonProperty("is_expanded")
        private Boolean isExpanded;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class GraphEdge {
        private String id;
        private String source;
        private String target;
        @JsonProperty("relation_type")
        private String relationType;
        private String description;
        private Double weight;
        @JsonProperty("article_count")
        private Integer articleCount;
        @JsonProperty("is_expanded")
        private Boolean isExpanded;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Community {
        private String id;
        private String name;
        private String summary;
        @JsonProperty("entity_count")
        private Integer entityCount;
        @JsonProperty("hub_entity")
        private String hubEntity;
        @JsonProperty("article_ids")
        private List<String> articleIds;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class VisualizationData {
        private List<GraphNode> nodes;
        private List<GraphEdge> edges;
        private List<Community> communities;
        private VisualizationStats stats;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class VisualizationStats {
        @JsonProperty("total_entities")
        private Integer totalEntities;
        @JsonProperty("seed_entities")
        private Integer seedEntities;
        @JsonProperty("expanded_entities")
        private Integer expandedEntities;
        @JsonProperty("total_relationships")
        private Integer totalRelationships;
        @JsonProperty("total_communities")
        private Integer totalCommunities;
    }
}