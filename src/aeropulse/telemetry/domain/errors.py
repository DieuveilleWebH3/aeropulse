"""Domain errors for the Telemetry bounded context."""


class TelemetryDomainError(ValueError):
    """Base class for Telemetry domain rule violations."""


class InvalidTelemetryId(TelemetryDomainError):
    """Raised when a telemetry sample identifier is not a UUID."""


class InvalidTelemetryEquipmentId(TelemetryDomainError):
    """Raised when a telemetry equipment identifier is not a UUID."""


class InvalidTelemetryMetric(TelemetryDomainError):
    """Raised when a telemetry metric name violates the Telemetry naming policy."""


class InvalidTelemetryValue(TelemetryDomainError):
    """Raised when a telemetry numeric value is not a finite float."""


class InvalidTelemetryUnit(TelemetryDomainError):
    """Raised when a telemetry unit violates the Telemetry unit policy."""


class InvalidTelemetryTimestamp(TelemetryDomainError):
    """Raised when a telemetry observation timestamp is invalid."""
