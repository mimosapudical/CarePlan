package com.careplan.api.careplan.dto;

import com.fasterxml.jackson.databind.JsonNode;

public record CarePlanStatusResponse(
        String id,
        String status,
        JsonNode content,
        String error) {
}
