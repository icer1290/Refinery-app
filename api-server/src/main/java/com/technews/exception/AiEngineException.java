package com.technews.exception;

public class AiEngineException extends RuntimeException {

    public AiEngineException(String message) {
        super(message);
    }

    public AiEngineException(String message, Throwable cause) {
        super(message, cause);
    }
}