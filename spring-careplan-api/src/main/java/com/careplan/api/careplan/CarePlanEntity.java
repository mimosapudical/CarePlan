package com.careplan.api.careplan;

import java.time.OffsetDateTime;
import java.util.UUID;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Immutable
@Table(name = "careplans_careplan")
public class CarePlanEntity {

    @Id
    @Column(name = "id", nullable = false, updatable = false)
    private UUID id;

    @Column(name = "status", nullable = false, length = 20)
    private String status;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "history", nullable = false, columnDefinition = "jsonb")
    private JsonNode history;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "payload", nullable = false, columnDefinition = "jsonb")
    private JsonNode payload;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "care_plan", columnDefinition = "jsonb")
    private JsonNode carePlan;

    @Column(name = "error", columnDefinition = "text")
    private String error;

    @Column(name = "queued_at")
    private OffsetDateTime queuedAt;

    @Column(name = "manual_retry_count", nullable = false)
    private Integer manualRetryCount;

    @Column(name = "last_manual_retry_at")
    private OffsetDateTime lastManualRetryAt;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    protected CarePlanEntity() {
    }

    CarePlanEntity(
            UUID id,
            String status,
            JsonNode history,
            JsonNode payload,
            JsonNode carePlan,
            String error,
            OffsetDateTime queuedAt,
            Integer manualRetryCount,
            OffsetDateTime lastManualRetryAt,
            OffsetDateTime createdAt,
            OffsetDateTime updatedAt) {
        this.id = id;
        this.status = status;
        this.history = history;
        this.payload = payload;
        this.carePlan = carePlan;
        this.error = error;
        this.queuedAt = queuedAt;
        this.manualRetryCount = manualRetryCount;
        this.lastManualRetryAt = lastManualRetryAt;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public UUID getId() {
        return id;
    }

    public String getStatus() {
        return status;
    }

    public JsonNode getHistory() {
        return history;
    }

    public JsonNode getPayload() {
        return payload;
    }

    public JsonNode getCarePlan() {
        return carePlan;
    }

    public String getError() {
        return error;
    }

    public OffsetDateTime getQueuedAt() {
        return queuedAt;
    }

    public Integer getManualRetryCount() {
        return manualRetryCount;
    }

    public OffsetDateTime getLastManualRetryAt() {
        return lastManualRetryAt;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }
}
