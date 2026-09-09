package com.careplan.api.careplan;

import java.time.Clock;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import com.careplan.api.careplan.dto.CarePlanResponse;
import com.careplan.api.careplan.dto.CarePlanStatusResponse;
import com.careplan.api.careplan.dto.OpsCarePlanResponse;
import com.careplan.api.careplan.exception.ApiExceptionHandler.BadRequestException;
import com.careplan.api.careplan.exception.ApiExceptionHandler.NotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class CarePlanService {

    private static final Set<String> VALID_STATUSES = Set.of(
            "pending", "processing", "completed", "failed");
    private static final int DEFAULT_STALE_MINUTES = 30;

    private final CarePlanRepository repository;
    private final Clock clock;

    public CarePlanService(CarePlanRepository repository, Clock clock) {
        this.repository = repository;
        this.clock = clock;
    }

    public CarePlanResponse getCarePlan(String rawId) {
        CarePlanEntity record = findRequired(rawId);
        return new CarePlanResponse(
                record.getId().toString(),
                record.getStatus(),
                record.getHistory(),
                record.getPayload(),
                "completed".equals(record.getStatus()) ? record.getCarePlan() : null,
                record.getError(),
                record.getQueuedAt(),
                record.getCreatedAt(),
                record.getUpdatedAt());
    }

    public CarePlanStatusResponse getCarePlanStatus(String rawId) {
        CarePlanEntity record = findRequired(rawId);
        return new CarePlanStatusResponse(
                record.getId().toString(),
                record.getStatus(),
                "completed".equals(record.getStatus()) ? record.getCarePlan() : null,
                "failed".equals(record.getStatus()) ? record.getError() : null);
    }

    public List<OpsCarePlanResponse> getOpsCarePlans(String rawStatus, String rawStaleMinutes) {
        String status = normalizeAndValidateStatus(rawStatus);
        int staleMinutes = parseStaleMinutes(rawStaleMinutes);
        OffsetDateTime cutoff = OffsetDateTime.now(clock).minusMinutes(staleMinutes);

        List<CarePlanRepository.OpsCarePlanView> records = status == null
                ? repository.findAllProjectedByOrderByCreatedAtDesc()
                : repository.findAllProjectedByStatusOrderByCreatedAtDesc(status);

        return records.stream()
                .map(record -> new OpsCarePlanResponse(
                        record.getId().toString(),
                        record.getStatus(),
                        record.getError(),
                        record.getQueuedAt(),
                        record.getCreatedAt(),
                        record.getUpdatedAt(),
                        record.getManualRetryCount(),
                        record.getLastManualRetryAt(),
                        isStale(record, cutoff)))
                .toList();
    }

    private CarePlanEntity findRequired(String rawId) {
        UUID id;
        try {
            id = UUID.fromString(rawId);
            if (!id.toString().equalsIgnoreCase(rawId)) {
                throw new IllegalArgumentException("non-canonical uuid");
            }
        } catch (IllegalArgumentException exception) {
            throw new BadRequestException("invalid uuid");
        }
        return repository.findById(id)
                .orElseThrow(() -> new NotFoundException("not found"));
    }

    private String normalizeAndValidateStatus(String rawStatus) {
        String status = rawStatus;
        if (status != null && status.isEmpty()) {
            status = null;
        }
        if (status != null && !VALID_STATUSES.contains(status)) {
            throw new BadRequestException("invalid status");
        }
        return status;
    }

    private int parseStaleMinutes(String rawStaleMinutes) {
        if (rawStaleMinutes == null) {
            return DEFAULT_STALE_MINUTES;
        }
        try {
            int staleMinutes = Integer.parseInt(rawStaleMinutes.trim());
            if (staleMinutes < 1) {
                throw new NumberFormatException("non-positive");
            }
            return staleMinutes;
        } catch (NumberFormatException exception) {
            throw new BadRequestException("stale_minutes must be a positive integer");
        }
    }

    private boolean isStale(CarePlanRepository.OpsCarePlanView record, OffsetDateTime cutoff) {
        boolean running = "pending".equals(record.getStatus()) || "processing".equals(record.getStatus());
        return running && record.getUpdatedAt().isBefore(cutoff);
    }
}
