package com.technews.dto.request;

import lombok.Data;
import java.util.List;

@Data
public class UserPreferenceRequest {

    private List<String> preferredCategories;

    private Boolean notificationEnabled;
}
