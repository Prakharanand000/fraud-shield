package com.fraudshield;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Entry point for the FraudShield real-time risk scoring service.
 *
 * <p>This Spring Boot microservice exposes a REST API that accepts transaction
 * payloads, delegates fraud probability scoring to a Python ML inference
 * service, and applies a business decision layer (BLOCK / REVIEW / APPROVE).
 */
@SpringBootApplication
public class FraudShieldApplication {

    public static void main(String[] args) {
        SpringApplication.run(FraudShieldApplication.class, args);
    }
}
