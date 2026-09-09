package com.careplan.api.careplan;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.UUID;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@SpringBootTest
@AutoConfigureMockMvc
@Testcontainers
class CarePlanRepositoryIntegrationTest {

    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine")
            .withDatabaseName("careplan")
            .withUsername("careplan")
            .withPassword("careplan");

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
        registry.add("spring.datasource.hikari.read-only", () -> "false");
        registry.add("spring.sql.init.mode", () -> "always");
        registry.add("spring.sql.init.schema-locations", () -> "classpath:schema.sql");
        registry.add("spring.jpa.hibernate.ddl-auto", () -> "validate");
    }

    @Autowired
    CarePlanRepository repository;

    @Autowired
    JdbcTemplate jdbcTemplate;

    @Autowired
    MockMvc mockMvc;

    @Autowired
    ObjectMapper objectMapper;

    @BeforeEach
    void clearRows() {
        jdbcTemplate.update("DELETE FROM careplans_careplan");
    }

    @Test
    void existingDjangoShapedCarePlanRowCanBeReadByUuid() {
        UUID id = UUID.randomUUID();
        insertRow(id, "pending", null, null, now().minusMinutes(2), now().minusMinutes(1));

        CarePlanEntity row = repository.findById(id).orElseThrow();

        org.junit.jupiter.api.Assertions.assertEquals(id, row.getId());
        org.junit.jupiter.api.Assertions.assertEquals("pending", row.getStatus());
        org.junit.jupiter.api.Assertions.assertEquals("Jane", row.getPayload().get("patient_first_name").asText());
    }

    @Test
    void completedRowExposesCarePlanAndStatusContent() throws Exception {
        UUID id = UUID.randomUUID();
        JsonNode carePlan = objectMapper.readTree("{\"goals\":[\"stay healthy\"],\"problem_list\":[\"hypertension\"]}");
        insertRow(id, "completed", carePlan, null, now().minusMinutes(4), now().minusMinutes(1));

        mockMvc.perform(get("/api/v1/careplans/{id}", id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.care_plan.goals[0]").value("stay healthy"));

        mockMvc.perform(get("/api/v1/careplans/{id}/status", id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content.problem_list[0]").value("hypertension"))
                .andExpect(jsonPath("$.error").value(org.hamcrest.Matchers.nullValue()));
    }

    @Test
    void failedRowExposesErrorAndNotContent() throws Exception {
        UUID id = UUID.randomUUID();
        insertRow(id, "failed", null, "generation failed", now().minusMinutes(5), now().minusMinutes(2));

        mockMvc.perform(get("/api/v1/careplans/{id}/status", id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").value(org.hamcrest.Matchers.nullValue()))
                .andExpect(jsonPath("$.error").value("generation failed"));
    }

    @Test
    void nonexistentUuidIs404AndMalformedUuidIs400() throws Exception {
        mockMvc.perform(get("/api/v1/careplans/{id}", UUID.randomUUID()))
                .andExpect(status().isNotFound());
        mockMvc.perform(get("/api/v1/careplans/not-a-uuid"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void statusFilterWorksAndKeepsCreatedAtDescendingOrder() throws Exception {
        UUID olderFailed = UUID.randomUUID();
        UUID newerFailed = UUID.randomUUID();
        UUID completed = UUID.randomUUID();
        insertRow(olderFailed, "failed", null, "old", now().minusMinutes(10), now().minusMinutes(9));
        insertRow(newerFailed, "failed", null, "new", now().minusMinutes(5), now().minusMinutes(4));
        insertRow(completed, "completed", objectMapper.createObjectNode(), null, now().minusMinutes(2), now().minusMinutes(1));

        mockMvc.perform(get("/api/v1/ops/careplans").queryParam("status", "failed"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.results.length()").value(2))
                .andExpect(jsonPath("$.results[0].id").value(newerFailed.toString()))
                .andExpect(jsonPath("$.results[1].id").value(olderFailed.toString()));
    }

    @Test
    void invalidStatusAndStaleMinutesReturn400() throws Exception {
        mockMvc.perform(get("/api/v1/ops/careplans").queryParam("status", "unknown"))
                .andExpect(status().isBadRequest());
        for (String value : List.of("0", "-3", "not-a-number")) {
            mockMvc.perform(get("/api/v1/ops/careplans").queryParam("stale_minutes", value))
                    .andExpect(status().isBadRequest());
        }
    }

    @Test
    void staleCalculationMatchesDjangoBehavior() throws Exception {
        UUID stalePending = UUID.randomUUID();
        UUID staleProcessing = UUID.randomUUID();
        UUID oldFailed = UUID.randomUUID();
        UUID freshPending = UUID.randomUUID();
        insertRow(stalePending, "pending", null, null, now().minusMinutes(60), now().minusMinutes(45));
        insertRow(staleProcessing, "processing", null, null, now().minusMinutes(60), now().minusMinutes(45));
        insertRow(oldFailed, "failed", null, "boom", now().minusMinutes(60), now().minusMinutes(45));
        insertRow(freshPending, "pending", null, null, now().minusMinutes(2), now().minusMinutes(1));

        String body = mockMvc.perform(get("/api/v1/ops/careplans").queryParam("stale_minutes", "30"))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        JsonNode results = objectMapper.readTree(body).get("results");
        java.util.Map<String, Boolean> staleById = new java.util.HashMap<>();
        results.forEach(row -> staleById.put(row.get("id").asText(), row.get("stale").asBoolean()));

        org.junit.jupiter.api.Assertions.assertTrue(staleById.get(stalePending.toString()));
        org.junit.jupiter.api.Assertions.assertTrue(staleById.get(staleProcessing.toString()));
        org.junit.jupiter.api.Assertions.assertFalse(staleById.get(oldFailed.toString()));
        org.junit.jupiter.api.Assertions.assertFalse(staleById.get(freshPending.toString()));
    }

    @Test
    void actuatorHealthSucceeds() throws Exception {
        mockMvc.perform(get("/actuator/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"));
    }

    private void insertRow(
            UUID id,
            String status,
            JsonNode carePlan,
            String error,
            OffsetDateTime createdAt,
            OffsetDateTime updatedAt) {
        String carePlanJson = carePlan == null ? null : carePlan.toString();
        jdbcTemplate.update("""
                INSERT INTO careplans_careplan (
                    id, status, history, payload, care_plan, error, queued_at,
                    manual_retry_count, last_manual_retry_at, created_at, updated_at
                ) VALUES (
                    ?, ?, CAST(? AS jsonb), CAST(? AS jsonb), CAST(? AS jsonb), ?, ?, ?, ?, ?, ?
                )
                """,
                id,
                status,
                "[\"pending\",\"" + status + "\"]",
                "{\"patient_first_name\":\"Jane\",\"patient_mrn\":\"MRN001\"}",
                carePlanJson,
                error,
                createdAt.plusSeconds(5),
                0,
                null,
                createdAt,
                updatedAt);
    }

    private static OffsetDateTime now() {
        return OffsetDateTime.now(ZoneOffset.UTC).withNano(0);
    }
}
