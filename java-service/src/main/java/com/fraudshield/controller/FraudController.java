package com.fraudshield.controller;

import com.fraudshield.model.RiskAssessment;
import com.fraudshield.model.Transaction;
import com.fraudshield.service.RiskScoringService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Public HTTP surface for the fraud risk scoring service.
 */
@RestController
@RequestMapping("/api/v1")
public class FraudController {

    private final RiskScoringService riskScoringService;

    public FraudController(RiskScoringService riskScoringService) {
        this.riskScoringService = riskScoringService;
    }

    /**
     * Scores a single transaction and returns a BLOCK / REVIEW / APPROVE decision.
     */
    @PostMapping("/assess")
    public ResponseEntity<RiskAssessment> assessTransaction(
            @Valid @RequestBody Transaction transaction) {
        return ResponseEntity.ok(riskScoringService.assess(transaction));
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("FraudShield API is running");
    }
}
