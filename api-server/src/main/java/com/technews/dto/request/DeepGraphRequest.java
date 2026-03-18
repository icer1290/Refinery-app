package com.technews.dto.request;

import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeepGraphRequest {

    @Size(min = 1, max = 20, message = "Article IDs must have between 1 and 20 elements")
    private List<String> articleIds;

    @Builder.Default
    private Integer maxHops = 2;

    @Builder.Default
    private Integer expansionLimit = 50;
}