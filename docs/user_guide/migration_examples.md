# Migration Examples: Before and After

This guide shows concrete examples of how nicestlog migration works with real code. Each example demonstrates the transformation from common logging patterns to nicestlog's structured approach.

## 🔄 Print Statement Migration

### Before: Basic Print Statements
```python
# old_app.py
def process_user(user_id, name):
    print(f"Processing user {user_id}")
    print("Starting validation...")
    
    if not name:
        print("Error: Name is required")
        return False
    
    print(f"User {name} validated successfully")
    print("Processing complete")
    return True

def main():
    print("Application starting")
    result = process_user(123, "Alice")
    print(f"Result: {result}")
```

### After: Structured Logging with nicestlog
```python
# new_app.py
import structlog

log = structlog.get_logger()

def process_user(user_id, name):
    log.info(
        "user-processing-started",
        _replace_msg="🔄 Processing user {user_id}",
        user_id=user_id
    )
    log.debug("validation-started", _replace_msg="Starting validation...")
    
    if not name:
        log.error(
            "validation-failed",
            _replace_msg="❌ Name is required for user {user_id}",
            user_id=user_id,
            error_type="missing_name"
        )
        return False
    
    log.info(
        "user-validated",
        _replace_msg="✅ User {name} validated successfully",
        name=name,
        user_id=user_id
    )
    log.info("processing-complete", _replace_msg="Processing complete")
    return True

def main():
    log.info("application-started", _replace_msg="🚀 Application starting")
    result = process_user(123, "Alice")
    log.info(
        "processing-result",
        _replace_msg="Result: {result}",
        result=result
    )
```

### Migration Command
```bash
# Analyze what would change
nicestlog migrate . --type print-to-structlog

# Apply the migration with backup
nicestlog migrate . --do-migrate --type print-to-structlog --backup
```

## 📊 Standard Logging Migration

### Before: Python's logging module
```python
# legacy_service.py
import logging

# Old logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        logger.info("UserService initialized")
    
    def create_user(self, email, password):
        logger.info(f"Creating user with email: {email}")
        
        if not self._validate_email(email):
            logger.error(f"Invalid email format: {email}")
            return None
        
        if len(password) < 8:
            logger.warning(f"Weak password for user: {email}")
        
        user_id = self._save_user(email, password)
        logger.info(f"User created successfully with ID: {user_id}")
        return user_id
    
    def _validate_email(self, email):
        logger.debug(f"Validating email: {email}")
        return "@" in email
    
    def _save_user(self, email, password):
        logger.debug("Saving user to database")
        return 12345
```

### After: Structured logging with nicestlog
```python
# modern_service.py
import structlog
import nicestlog

# Initialize nicestlog
nicestlog.init_logging(
    verbose=True,
    syslog_identifier="user-service",
    log_format="console"
)

log = structlog.get_logger()

class UserService:
    def __init__(self):
        log.info(
            "service-initialized",
            _replace_msg="🔧 UserService initialized",
            service="UserService"
        )
    
    def create_user(self, email, password):
        log.info(
            "user-creation-started",
            _replace_msg="👤 Creating user with email: {email}",
            email=email,
            action="create_user"
        )
        
        if not self._validate_email(email):
            log.error(
                "email-validation-failed",
                _replace_msg="❌ Invalid email format: {email}",
                email=email,
                error_type="invalid_format"
            )
            return None
        
        if len(password) < 8:
            log.warning(
                "weak-password-detected",
                _replace_msg="⚠️ Weak password for user: {email}",
                email=email,
                password_length=len(password),
                min_length=8
            )
        
        user_id = self._save_user(email, password)
        log.info(
            "user-created-successfully",
            _replace_msg="✅ User created successfully with ID: {user_id}",
            user_id=user_id,
            email=email
        )
        return user_id
    
    def _validate_email(self, email):
        log.debug(
            "email-validation",
            _replace_msg="🔍 Validating email: {email}",
            email=email
        )
        return "@" in email
    
    def _save_user(self, email, password):
        log.debug(
            "database-save",
            _replace_msg="💾 Saving user to database",
            email=email
        )
        return 12345
```

### Migration Command
```bash
# Interactive migration for review
nicestlog migrate . --do-migrate --type logging-to-structlog --interactive

# Or automatic with backup
nicestlog migrate . --do-migrate --type logging-to-structlog --backup
```

## 🎯 Eliot Integration Migration

### Before: Basic function calls
```python
# sync_service.py
def sync_data(source, destination):
    print(f"Starting sync from {source} to {destination}")
    
    try:
        data = fetch_data(source)
        print(f"Fetched {len(data)} records")
        
        processed = process_data(data)
        print(f"Processed {len(processed)} records")
        
        save_data(destination, processed)
        print("Sync completed successfully")
        
    except Exception as e:
        print(f"Sync failed: {e}")
        raise

def fetch_data(source):
    print(f"Connecting to {source}")
    # Simulate data fetching
    return [{"id": i, "data": f"item_{i}"} for i in range(100)]

def process_data(data):
    print("Processing data...")
    # Simulate processing
    return [{"id": item["id"], "processed": True} for item in data]

def save_data(destination, data):
    print(f"Saving to {destination}")
    # Simulate saving
    pass
```

### After: Eliot action tracing with nicestlog
```python
# modern_sync_service.py
import structlog
import nicestlog
from nicestlog.eliot_integration import eliot_action, eliot_message

# Initialize nicestlog with Eliot support
nicestlog.init_logging(
    verbose=True,
    syslog_identifier="sync-service",
    log_format="console"
)

log = structlog.get_logger()

@eliot_action
def sync_data(source, destination):
    """Sync data from source to destination with full action tracing."""
    log.info(
        "sync-started",
        _replace_msg="🔄 Starting sync from {source} to {destination}",
        source=source,
        destination=destination
    )
    
    try:
        data = fetch_data(source)
        log.info(
            "data-fetched",
            _replace_msg="📥 Fetched {count} records",
            count=len(data),
            source=source
        )
        
        processed = process_data(data)
        log.info(
            "data-processed",
            _replace_msg="⚙️ Processed {count} records",
            count=len(processed)
        )
        
        save_data(destination, processed)
        log.info(
            "sync-completed",
            _replace_msg="✅ Sync completed successfully",
            records_synced=len(processed)
        )
        
    except Exception as e:
        log.error(
            "sync-failed",
            _replace_msg="❌ Sync failed: {error}",
            error=str(e),
            source=source,
            destination=destination
        )
        raise

@eliot_action
def fetch_data(source):
    """Fetch data from source with action tracing."""
    eliot_message(
        "connection-attempt",
        _replace_msg="🔌 Connecting to {source}",
        source=source
    )
    
    # Simulate data fetching
    data = [{"id": i, "data": f"item_{i}"} for i in range(100)]
    
    eliot_message(
        "data-retrieved",
        _replace_msg="📊 Retrieved {count} records from {source}",
        count=len(data),
        source=source
    )
    
    return data

@eliot_action
def process_data(data):
    """Process data with action tracing."""
    eliot_message(
        "processing-started",
        _replace_msg="⚙️ Processing {count} records...",
        count=len(data)
    )
    
    # Simulate processing
    processed = [{"id": item["id"], "processed": True} for item in data]
    
    eliot_message(
        "processing-completed",
        _replace_msg="✅ Processing completed",
        input_count=len(data),
        output_count=len(processed)
    )
    
    return processed

@eliot_action
def save_data(destination, data):
    """Save data to destination with action tracing."""
    eliot_message(
        "save-started",
        _replace_msg="💾 Saving {count} records to {destination}",
        count=len(data),
        destination=destination
    )
    
    # Simulate saving
    
    eliot_message(
        "save-completed",
        _replace_msg="✅ Successfully saved to {destination}",
        destination=destination,
        records_saved=len(data)
    )
```

### Migration Command
```bash
# Check for eliot integration opportunities
nicestlog check . --pattern eliot

# Apply eliot-style transformations
nicestlog check . --fix --pattern action
```

## 🔧 Other Logging Libraries

### Loguru Migration Example

**Before: Loguru**
```python
# loguru_app.py
from loguru import logger

logger.add("app.log", rotation="500 MB")

def process_order(order_id, items):
    logger.info(f"Processing order {order_id} with {len(items)} items")
    
    for item in items:
        logger.debug(f"Processing item: {item['name']}")
        
        if item['price'] < 0:
            logger.error(f"Invalid price for item {item['name']}: {item['price']}")
            continue
    
    logger.success(f"Order {order_id} processed successfully")
```

**After: nicestlog**
```python
# nicestlog_app.py
import structlog
import nicestlog

nicestlog.init_logging(
    verbose=True,
    log_file="app.log",
    log_file_max_size=500,  # MB
    syslog_identifier="order-service"
)

log = structlog.get_logger()

def process_order(order_id, items):
    log.info(
        "order-processing-started",
        _replace_msg="📦 Processing order {order_id} with {item_count} items",
        order_id=order_id,
        item_count=len(items)
    )
    
    for item in items:
        log.debug(
            "item-processing",
            _replace_msg="🔍 Processing item: {item_name}",
            item_name=item['name'],
            order_id=order_id
        )
        
        if item['price'] < 0:
            log.error(
                "invalid-item-price",
                _replace_msg="❌ Invalid price for item {item_name}: {price}",
                item_name=item['name'],
                price=item['price'],
                order_id=order_id
            )
            continue
    
    log.info(
        "order-processed-successfully",
        _replace_msg="✅ Order {order_id} processed successfully",
        order_id=order_id,
        items_processed=len(items)
    )
```

### Sentry Integration Example

**Before: Direct Sentry calls**
```python
# sentry_app.py
import sentry_sdk

sentry_sdk.init(dsn="your-dsn-here")

def handle_payment(amount, user_id):
    print(f"Processing payment of ${amount} for user {user_id}")
    
    try:
        # Payment processing logic
        if amount <= 0:
            raise ValueError("Invalid payment amount")
        
        # Process payment...
        print(f"Payment successful for user {user_id}")
        
    except Exception as e:
        sentry_sdk.capture_exception(e)
        print(f"Payment failed: {e}")
        raise
```

**After: nicestlog with Sentry integration**
```python
# nicestlog_sentry_app.py
import structlog
import nicestlog
import sentry_sdk
from sentry_sdk.integrations.structlog import StructlogIntegration

# Initialize Sentry with structlog integration
sentry_sdk.init(
    dsn="your-dsn-here",
    integrations=[StructlogIntegration()]
)

# Initialize nicestlog
nicestlog.init_logging(
    verbose=True,
    syslog_identifier="payment-service"
)

log = structlog.get_logger()

def handle_payment(amount, user_id):
    log.info(
        "payment-processing-started",
        _replace_msg="💳 Processing payment of ${amount} for user {user_id}",
        amount=amount,
        user_id=user_id,
        currency="USD"
    )
    
    try:
        # Payment processing logic
        if amount <= 0:
            log.error(
                "invalid-payment-amount",
                _replace_msg="❌ Invalid payment amount: ${amount}",
                amount=amount,
                user_id=user_id
            )
            raise ValueError("Invalid payment amount")
        
        # Process payment...
        log.info(
            "payment-successful",
            _replace_msg="✅ Payment successful for user {user_id}",
            user_id=user_id,
            amount=amount,
            transaction_id="txn_123456"
        )
        
    except Exception as e:
        log.error(
            "payment-failed",
            _replace_msg="💥 Payment failed: {error}",
            error=str(e),
            user_id=user_id,
            amount=amount,
            exc_info=True  # This will be captured by Sentry
        )
        raise
```

## 🚀 Migration Commands Summary

| Migration Type | Command | Use Case |
|---|---|---|
| **Print to Structlog** | `nicestlog migrate . --do-migrate --type print-to-structlog` | Convert print() statements |
| **Logging to Structlog** | `nicestlog migrate . --do-migrate --type logging-to-structlog --interactive` | Convert standard logging |
| **Format Strings** | `nicestlog migrate . --do-migrate --type format-strings` | Convert f-strings to structured |
| **Analysis Only** | `nicestlog migrate .` | Analyze without changes |
| **Interactive Mode** | `nicestlog migrate . --do-migrate --interactive` | Review each change |
| **With Backup** | `nicestlog migrate . --do-migrate --backup` | Create backup files |

## 🔍 Validation Commands

After migration, validate your changes:

```bash
# Check code quality
nicestlog check .

# Fix any remaining issues
nicestlog check . --fix

# Validate translations
nicestlog i18n check src/

# Run demos to see results
nicestlog tools demo
```

## 📚 Next Steps

1. **Initialize Configuration**: `nicestlog init .`
2. **Choose Migration Type**: Based on your current logging approach
3. **Run Analysis**: `nicestlog migrate .` to see what would change
4. **Apply Migration**: Add `--do-migrate` flag when ready
5. **Validate Results**: Use `nicestlog check` and `nicestlog demo`

For more examples and advanced patterns, see:
- [CLI Migration Guide](cli_migration_guide.md)
- [Best Practices](best_practices.md)
- [Advanced Features](advanced_features.md)