package com.careplan.api.careplan.dto;

import java.time.OffsetDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

public record OpsCarePlanResponse(
        String id,
        String status,
        String error,
        @JsonProperty("queued_at") OffsetDateTime queuedAt,
        @JsonProperty("created_at") OffsetDateTime createdAt,
        @JsonProperty("updated_at") OffsetDateTime updatedAt,
        @JsonProperty("manual_retry_count") Integer manualRetryCount,
        @JsonProperty("last_manual_retry_at") OffsetDateTime lastManualRetryAt,
        boolean stale) {
}
