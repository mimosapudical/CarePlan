package com.careplan.api.careplan;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.repository.Repository;

public interface CarePlanRepository extends Repository<CarePlanEntity, UUID> {

    Optional<CarePlanEntity> findById(UUID id);

    List<OpsCarePlanView> findAllProjectedByOrderByCreatedAtDesc();

    List<OpsCarePlanView> findAllProjectedByStatusOrderByCreatedAtDesc(String status);

    interface OpsCarePlanView {
        UUID getId();

        String getStatus();

        String getError();

        OffsetDateTime getQueuedAt();

        OffsetDateTime getCreatedAt();

        OffsetDateTime getUpdatedAt();

        Integer getManualRetryCount();

        OffsetDateTime getLastManualRetryAt();
    }
}
