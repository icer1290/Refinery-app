package com.technews.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "deepgraph_analyses")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DeepGraphAnalysis {

    @Id
    @GeneratedValue
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "article_ids", nullable = false, columnDefinition = "uuid[]")
    private List<UUID> articleIds;

    @Column(columnDefinition = "TEXT")
    private String report;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "visualization_data", columnDefinition = "jsonb")
    private Map<String, Object> visualizationData;

    @Column(name = "max_hops")
    private Integer maxHops;

    @Column(name = "expansion_limit")
    private Integer expansionLimit;

    @Column(name = "created_at")
    private LocalDateTime createdAt;
}