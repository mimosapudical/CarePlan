package com.careplan.api.careplan;

import static org.hamcrest.Matchers.containsString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.Clock;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

import com.careplan.api.careplan.exception.ApiExceptionHandler;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

class CarePlanControllerTest {

    private static final Instant NOW = Instant.parse("2026-09-09T04:00:00Z");

    private CarePlanRepository repository;
    private MockMvc mockMvc;
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        repository = mock(CarePlanRepository.class);
        objectMapper = new ObjectMapper()
                .registerModule(new JavaTimeModule())
                .setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)
                .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        Clock clock = Clock.fixed(NOW, ZoneOffset.UTC);
        CarePlanService service = new CarePlanService(repository, clock);
        mockMvc = MockMvcBuilders.standaloneSetup(new CarePlanController(service))
                .setControllerAdvice(new ApiExceptionHandler())
                .setMessageConverters(new MappingJackson2HttpMessageConverter(objectMapper))
                .build();
    }

    @Test
    void recordResponseMatchesDjangoRecordToDictContract() throws Exception {
        UUID id = UUID.randomUUID();
        CarePlanEntity record = completedRecord(id);
        when(repository.findById(id)).thenReturn(Optional.of(record));

        String body = mockMvc.perform(get("/api/v1/careplans/{id}", id))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();

        JsonNode json = objectMapper.readTree(body);
        assertFields(json, Set.of(
                "id", "status", "history", "payload", "care_plan", "error",
                "queued_at", "created_at", "updated_at"));
        org.junit.jupiter.api.Assertions.assertEquals(id.toString(), json.get("id").asText());
        org.junit.jupiter.api.Assertions.assertEquals("completed", json.get("status").asText());
        org.junit.jupiter.api.Assertions.assertEquals("goal-a", json.at("/care_plan/goals/0").asText());
        org.junit.jupiter.api.Assertions.assertEquals("Jane", json.at("/payload/patient_first_name").asText());
        org.junit.jupiter.api.Assertions.assertTrue(json.get("error").isNull());
        org.junit.jupiter.api.Assertions.assertTrue(OffsetDateTime.parse(json.get("created_at").asText()).toInstant()
                .equals(Instant.parse("2026-09-09T02:00:00Z")));
    }

    @Test
    void statusResponseMatchesDjangoStatusToDictContractForCompletedAndFailed() throws Exception {
        UUID completedId = UUID.randomUUID();
        when(repository.findById(completedId)).thenReturn(Optional.of(completedRecord(completedId)));
        JsonNode completed = objectMapper.readTree(mockMvc.perform(get("/api/v1/careplans/{id}/status", completedId))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString());

        assertFields(completed, Set.of("id", "status", "content", "error"));
        org.junit.jupiter.api.Assertions.assertEquals("goal-a", completed.at("/content/goals/0").asText());
        org.junit.jupiter.api.Assertions.assertTrue(completed.get("error").isNull());

        UUID failedId = UUID.randomUUID();
        CarePlanEntity failed = record(failedId, "failed", null, "worker unavailable",
                OffsetDateTime.ofInstant(NOW.minusSeconds(3600), ZoneOffset.UTC));
        when(repository.findById(failedId)).thenReturn(Optional.of(failed));
        JsonNode failedJson = objectMapper.readTree(mockMvc.perform(get("/api/v1/careplans/{id}/status", failedId))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString());

        assertFields(failedJson, Set.of("id", "status", "content", "error"));
        org.junit.jupiter.api.Assertions.assertTrue(failedJson.get("content").isNull());
        org.junit.jupiter.api.Assertions.assertEquals("worker unavailable", failedJson.get("error").asText());
    }

    @Test
    void opsResponseMatchesDjangoOpsRecordToDictContractAndStatusFilter() throws Exception {
        UUID id = UUID.randomUUID();
        CarePlanRepository.OpsCarePlanView failed = opsView(
                id, "failed", "boom", OffsetDateTime.ofInstant(NOW.minusSeconds(7200), ZoneOffset.UTC));
        when(repository.findAllProjectedByStatusOrderByCreatedAtDesc("failed")).thenReturn(List.of(failed));

        JsonNode body = objectMapper.readTree(mockMvc.perform(get("/api/v1/ops/careplans")
                        .queryParam("status", "failed")
                        .queryParam("stale_minutes", "30"))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString());

        JsonNode row = body.get("results").get(0);
        assertFields(row, Set.of(
                "id", "status", "error", "queued_at", "created_at", "updated_at",
                "manual_retry_count", "last_manual_retry_at", "stale"));
        org.junit.jupiter.api.Assertions.assertEquals("failed", row.get("status").asText());
        org.junit.jupiter.api.Assertions.assertFalse(row.get("stale").asBoolean());
        org.junit.jupiter.api.Assertions.assertFalse(row.has("payload"));
        org.junit.jupiter.api.Assertions.assertFalse(row.has("care_plan"));
        verify(repository).findAllProjectedByStatusOrderByCreatedAtDesc("failed");
        verify(repository, never()).findAllProjectedByOrderByCreatedAtDesc();
    }

    @Test
    void nonCompletedDetailHidesCarePlanLikeDjangoSerializer() throws Exception {
        UUID id = UUID.randomUUID();
        ObjectNode hiddenPlan = objectMapper.createObjectNode().put("secret", "not-yet-complete");
        when(repository.findById(id)).thenReturn(Optional.of(record(
                id, "processing", hiddenPlan, null,
                OffsetDateTime.ofInstant(NOW.minusSeconds(60), ZoneOffset.UTC))));

        mockMvc.perform(get("/api/v1/careplans/{id}", id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.care_plan").value(org.hamcrest.Matchers.nullValue()));
    }

    @Test
    void nonexistentUuidReturns404() throws Exception {
        UUID id = UUID.randomUUID();
        when(repository.findById(id)).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/v1/careplans/{id}", id))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error").value("not found"));
    }

    @Test
    void malformedUuidReturns400() throws Exception {
        mockMvc.perform(get("/api/v1/careplans/not-a-uuid"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("invalid uuid"));
    }

    @Test
    void invalidStatusReturns400() throws Exception {
        mockMvc.perform(get("/api/v1/ops/careplans").queryParam("status", "unknown"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("invalid status"));
        verify(repository, never()).findAllProjectedByOrderByCreatedAtDesc();
    }

    @Test
    void staleMinutesMustBePositiveInteger() throws Exception {
        for (String value : List.of("0", "-1", "oops", "")) {
            mockMvc.perform(get("/api/v1/ops/careplans").queryParam("stale_minutes", value))
                    .andExpect(status().isBadRequest())
                    .andExpect(content().string(containsString("stale_minutes must be a positive integer")));
        }
    }

    @Test
    void staleCalculationMatchesDjangoPendingProcessingRuleAndStrictCutoff() throws Exception {
        OffsetDateTime now = OffsetDateTime.ofInstant(NOW, ZoneOffset.UTC);
        CarePlanRepository.OpsCarePlanView stalePending = opsView(UUID.randomUUID(), "pending", null, now.minusMinutes(31));
        CarePlanRepository.OpsCarePlanView staleProcessing = opsView(UUID.randomUUID(), "processing", null, now.minusMinutes(31));
        CarePlanRepository.OpsCarePlanView exactlyAtCutoff = opsView(UUID.randomUUID(), "pending", null, now.minusMinutes(30));
        CarePlanRepository.OpsCarePlanView oldFailed = opsView(UUID.randomUUID(), "failed", "boom", now.minusMinutes(90));
        when(repository.findAllProjectedByOrderByCreatedAtDesc()).thenReturn(
                List.of(stalePending, staleProcessing, exactlyAtCutoff, oldFailed));

        JsonNode results = objectMapper.readTree(mockMvc.perform(get("/api/v1/ops/careplans")
                        .queryParam("stale_minutes", "30"))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString()).get("results");

        org.junit.jupiter.api.Assertions.assertTrue(results.get(0).get("stale").asBoolean());
        org.junit.jupiter.api.Assertions.assertTrue(results.get(1).get("stale").asBoolean());
        org.junit.jupiter.api.Assertions.assertFalse(results.get(2).get("stale").asBoolean());
        org.junit.jupiter.api.Assertions.assertFalse(results.get(3).get("stale").asBoolean());
    }

    private CarePlanRepository.OpsCarePlanView opsView(
            UUID id, String status, String error, OffsetDateTime updatedAt) {
        CarePlanRepository.OpsCarePlanView view = mock(CarePlanRepository.OpsCarePlanView.class);
        when(view.getId()).thenReturn(id);
        when(view.getStatus()).thenReturn(status);
        when(view.getError()).thenReturn(error);
        when(view.getQueuedAt()).thenReturn(OffsetDateTime.parse("2026-09-09T02:01:00Z"));
        when(view.getCreatedAt()).thenReturn(OffsetDateTime.parse("2026-09-09T02:00:00Z"));
        when(view.getUpdatedAt()).thenReturn(updatedAt);
        when(view.getManualRetryCount()).thenReturn(0);
        when(view.getLastManualRetryAt()).thenReturn(null);
        return view;
    }

    private CarePlanEntity completedRecord(UUID id) {
        ObjectNode carePlan = objectMapper.createObjectNode();
        carePlan.putArray("goals").add("goal-a");
        return record(id, "completed", carePlan, null,
                OffsetDateTime.ofInstant(NOW.minusSeconds(1200), ZoneOffset.UTC));
    }

    private CarePlanEntity record(
            UUID id,
            String status,
            JsonNode carePlan,
            String error,
            OffsetDateTime updatedAt) {
        ArrayNode history = objectMapper.createArrayNode().add("pending").add(status);
        ObjectNode payload = objectMapper.createObjectNode()
                .put("patient_first_name", "Jane")
                .put("patient_mrn", "MRN001");
        OffsetDateTime createdAt = OffsetDateTime.parse("2026-09-09T02:00:00Z");
        return new CarePlanEntity(
                id,
                status,
                history,
                payload,
                carePlan,
                error,
                OffsetDateTime.parse("2026-09-09T02:01:00Z"),
                0,
                null,
                createdAt,
                updatedAt);
    }

    private static void assertFields(JsonNode node, Set<String> expected) {
        Set<String> actual = new HashSet<>();
        node.fieldNames().forEachRemaining(actual::add);
        org.junit.jupiter.api.Assertions.assertEquals(expected, actual);
    }
}
