package com.technews.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeepGraphAnalysisListResponse {

    private List<DeepGraphAnalysisResponse> analyses;
    private long total;
    private int page;
    private int pageSize;
}