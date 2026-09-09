package com.careplan.api.careplan;

import java.util.List;
import java.util.Map;

import com.careplan.api.careplan.dto.CarePlanResponse;
import com.careplan.api.careplan.dto.CarePlanStatusResponse;
import com.careplan.api.careplan.dto.OpsCarePlanResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
public class CarePlanController {

    private final CarePlanService service;

    public CarePlanController(CarePlanService service) {
        this.service = service;
    }

    @GetMapping("/careplans/{id}")
    public CarePlanResponse getCarePlan(@PathVariable String id) {
        return service.getCarePlan(id);
    }

    @GetMapping("/careplans/{id}/status")
    public CarePlanStatusResponse getCarePlanStatus(@PathVariable String id) {
        return service.getCarePlanStatus(id);
    }

    @GetMapping("/ops/careplans")
    public Map<String, List<OpsCarePlanResponse>> getOpsCarePlans(
            @RequestParam(required = false) String status,
            @RequestParam(name = "stale_minutes", required = false) String staleMinutes) {
        return Map.of("results", service.getOpsCarePlans(status, staleMinutes));
    }
}
