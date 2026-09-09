package com.careplan.api.careplan.dto;

import java.time.OffsetDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

public record CarePlanResponse(
        String id,
        String status,
        JsonNode history,
        JsonNode payload,
        @JsonProperty("care_plan") JsonNode carePlan,
        String error,
        @JsonProperty("queued_at") OffsetDateTime queuedAt,
        @JsonProperty("created_at") OffsetDateTime createdAt,
        @JsonProperty("updated_at") OffsetDateTime updatedAt) {
}
