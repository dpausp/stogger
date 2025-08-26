#!/usr/bin/env python3
"""
Practical migration examples showing before/after code transformations.

This file demonstrates real-world migration scenarios that users can
run and see the actual transformations in action.
"""

import sys
import tempfile
from pathlib import Path


def create_example_files():
    """Create example files showing different logging patterns."""

    # Example 1: Print statements
    print_example = '''#!/usr/bin/env python3
"""Example with print statements - BEFORE migration."""

def process_user_data(user_id, name, email):
    print(f"Processing user {user_id}")
    print("Starting validation...")
    
    if not email or "@" not in email:
        print(f"Error: Invalid email {email}")
        return False
    
    if len(name) < 2:
        print(f"Error: Name too short: {name}")
        return False
    
    print(f"User {name} ({email}) validated successfully")
    print("Processing complete")
    return True

def main():
    print("=== User Processing Demo ===")
    
    users = [
        (1, "Alice", "alice@example.com"),
        (2, "Bob", "invalid-email"),
        (3, "X", "x@test.com"),
    ]
    
    for user_id, name, email in users:
        print(f"\\n--- Processing User {user_id} ---")
        result = process_user_data(user_id, name, email)
        print(f"Result: {'SUCCESS' if result else 'FAILED'}")
    
    print("\\n=== Demo Complete ===")

if __name__ == "__main__":
    main()
'''

    # Example 2: Standard logging
    logging_example = '''#!/usr/bin/env python3
"""Example with standard logging - BEFORE migration."""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class OrderProcessor:
    def __init__(self):
        logger.info("OrderProcessor initialized")
        self.processed_count = 0
    
    def process_order(self, order_id, items, customer_id):
        logger.info(f"Processing order {order_id} for customer {customer_id}")
        
        if not items:
            logger.error(f"Order {order_id} has no items")
            return False
        
        total_price = 0
        for item in items:
            logger.debug(f"Processing item: {item['name']} - ${item['price']}")
            
            if item['price'] <= 0:
                logger.warning(f"Invalid price for {item['name']}: ${item['price']}")
                continue
            
            total_price += item['price']
        
        if total_price == 0:
            logger.error(f"Order {order_id} has zero total")
            return False
        
        logger.info(f"Order {order_id} processed successfully. Total: ${total_price}")
        self.processed_count += 1
        return True
    
    def get_stats(self):
        logger.info(f"Total orders processed: {self.processed_count}")
        return {"processed": self.processed_count}

def main():
    logger.info("Starting order processing demo")
    
    processor = OrderProcessor()
    
    orders = [
        {
            "id": "ORD-001",
            "customer_id": "CUST-123",
            "items": [
                {"name": "Widget A", "price": 10.99},
                {"name": "Widget B", "price": 15.50}
            ]
        },
        {
            "id": "ORD-002", 
            "customer_id": "CUST-456",
            "items": []  # Empty order
        },
        {
            "id": "ORD-003",
            "customer_id": "CUST-789", 
            "items": [
                {"name": "Widget C", "price": -5.00},  # Invalid price
                {"name": "Widget D", "price": 20.00}
            ]
        }
    ]
    
    for order in orders:
        logger.info(f"--- Processing Order {order['id']} ---")
        result = processor.process_order(
            order['id'], 
            order['items'], 
            order['customer_id']
        )
        logger.info(f"Order {order['id']} result: {'SUCCESS' if result else 'FAILED'}")
    
    stats = processor.get_stats()
    logger.info(f"Final stats: {stats}")
    logger.info("Demo complete")

if __name__ == "__main__":
    main()
'''

    # Example 3: Mixed patterns (realistic scenario)
    mixed_example = '''#!/usr/bin/env python3
"""Example with mixed logging patterns - BEFORE migration."""

import logging
import sys
from datetime import datetime

# Mix of logging configurations
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class DataSyncService:
    def __init__(self, source_url, target_url):
        self.source_url = source_url
        self.target_url = target_url
        print(f"DataSyncService initialized")
        print(f"Source: {source_url}")
        print(f"Target: {target_url}")
    
    def sync_data(self):
        print("=== Starting Data Sync ===")
        start_time = datetime.now()
        
        try:
            # Fetch data
            print("Fetching data from source...")
            data = self._fetch_data()
            logger.info(f"Fetched {len(data)} records")
            
            # Validate data
            print("Validating data...")
            valid_data = self._validate_data(data)
            logger.warning(f"Filtered out {len(data) - len(valid_data)} invalid records")
            
            # Transform data
            print("Transforming data...")
            transformed_data = self._transform_data(valid_data)
            
            # Save data
            print("Saving data to target...")
            self._save_data(transformed_data)
            
            duration = (datetime.now() - start_time).total_seconds()
            print(f"Sync completed in {duration:.2f} seconds")
            logger.info(f"Successfully synced {len(transformed_data)} records")
            
            return True
            
        except Exception as e:
            print(f"Sync failed: {e}", file=sys.stderr)
            logger.error(f"Sync operation failed: {str(e)}")
            return False
    
    def _fetch_data(self):
        # Simulate fetching data
        print(f"Connecting to {self.source_url}")
        
        # Simulate some issues
        if "unreliable" in self.source_url:
            logger.warning("Source marked as unreliable")
        
        data = [
            {"id": 1, "name": "Record 1", "value": 100},
            {"id": 2, "name": "Record 2", "value": None},  # Invalid
            {"id": 3, "name": "", "value": 300},  # Invalid
            {"id": 4, "name": "Record 4", "value": 400},
        ]
        
        print(f"Retrieved {len(data)} raw records")
        return data
    
    def _validate_data(self, data):
        valid_records = []
        
        for record in data:
            if not record.get("name"):
                print(f"Skipping record {record['id']}: missing name")
                continue
            
            if record.get("value") is None:
                print(f"Skipping record {record['id']}: missing value")
                continue
            
            valid_records.append(record)
        
        logger.debug(f"Validation complete: {len(valid_records)} valid records")
        return valid_records
    
    def _transform_data(self, data):
        transformed = []
        
        for record in data:
            # Simple transformation
            transformed_record = {
                "external_id": record["id"],
                "display_name": record["name"].upper(),
                "amount": record["value"] * 1.1,  # Add 10%
                "processed_at": datetime.now().isoformat()
            }
            transformed.append(transformed_record)
        
        print(f"Transformed {len(transformed)} records")
        return transformed
    
    def _save_data(self, data):
        print(f"Saving {len(data)} records to {self.target_url}")
        
        # Simulate saving
        for i, record in enumerate(data):
            if i % 10 == 0:  # Progress indicator
                print(f"Saved {i}/{len(data)} records...")
        
        logger.info(f"All {len(data)} records saved successfully")

def main():
    print("=== Data Sync Demo ===")
    
    service = DataSyncService(
        source_url="https://api.source.com/data",
        target_url="https://api.target.com/import"
    )
    
    success = service.sync_data()
    
    if success:
        print("✅ Sync completed successfully")
    else:
        print("❌ Sync failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    return {
        "print_example.py": print_example,
        "logging_example.py": logging_example,
        "mixed_example.py": mixed_example,
    }


def demonstrate_migration():
    """Demonstrate the migration process with real examples."""

    print("🎯 Nicestlog Migration Examples")
    print("=" * 50)

    # Create temporary directory
    with tempfile.TemporaryDirectory(prefix="nicestlog_migration_") as temp_dir:
        temp_path = Path(temp_dir)
        print(f"📁 Working in: {temp_path}")

        # Create example files
        examples = create_example_files()

        for filename, content in examples.items():
            file_path = temp_path / filename
            file_path.write_text(content)
            print(f"📝 Created: {filename}")

        print("\n🔍 Analysis Phase")
        print("-" * 30)

        # Show what files we have
        print("Example files created:")
        for filename in examples.keys():
            file_path = temp_path / filename
            lines = len(file_path.read_text().split("\n"))
            print(f"  • {filename} ({lines} lines)")

        print("\n📊 To analyze these files, run:")
        print(f"  cd {temp_path}")
        print("  nicestlog migrate .")

        print("\n🔄 To migrate these files, run:")
        print(f"  cd {temp_path}")
        print("  nicestlog migrate . --do-migrate --type print-to-structlog --backup")

        print("\n🎬 To see the actual migration in action:")
        print("  # Run the original examples")
        for filename in examples.keys():
            print(f"  python {temp_path / filename}")

        print("\n  # Then migrate and run again to see the difference")
        print(f"  nicestlog migrate {temp_path} --do-migrate --type print-to-structlog")

        print(f"\n📚 Example files will remain in: {temp_path}")
        print("   (until system cleanup)")

        # Keep the directory path for user reference
        return temp_path


def show_library_comparison():
    """Show comparison of different logging libraries and migration paths."""

    print("\n📚 Logging Library Migration Paths")
    print("=" * 50)

    libraries = {
        "print() statements": {
            "migration_type": "print-to-structlog",
            "difficulty": "Easy",
            "command": "nicestlog migrate . --do-migrate --type print-to-structlog",
            "notes": "Automatic transformation, very safe",
        },
        "Standard logging": {
            "migration_type": "logging-to-structlog",
            "difficulty": "Medium",
            "command": "nicestlog migrate . --do-migrate --type logging-to-structlog --interactive",
            "notes": "Interactive review recommended",
        },
        "Loguru": {
            "migration_type": "manual + enhancement",
            "difficulty": "Medium",
            "command": "nicestlog check . --ast --fix",
            "notes": "Manual conversion + nicestlog enhancement",
        },
        "Eliot": {
            "migration_type": "enhancement",
            "difficulty": "Easy",
            "command": "Already compatible! Use nicestlog.eliot_integration",
            "notes": "Nicestlog enhances Eliot with beautiful output",
        },
        "Sentry": {
            "migration_type": "integration",
            "difficulty": "Easy",
            "command": "Use Sentry's StructlogIntegration",
            "notes": "Works seamlessly with nicestlog",
        },
        "Rich logging": {
            "migration_type": "enhancement",
            "difficulty": "Easy",
            "command": "nicestlog already uses Rich for beautiful output",
            "notes": "Complementary - nicestlog uses Rich internally",
        },
    }

    for library, info in libraries.items():
        print(f"\n🔧 {library}")
        print(f"   Migration: {info['migration_type']}")
        print(f"   Difficulty: {info['difficulty']}")
        print(f"   Command: {info['command']}")
        print(f"   Notes: {info['notes']}")

    print("\n💡 Pro Tips:")
    print("   • Always run 'nicestlog migrate .' first to analyze")
    print("   • Use --backup flag for safety")
    print("   • Use --interactive for complex projects")
    print("   • Run 'nicestlog check . --ast' after migration")


def main():
    """Main demo function."""

    if len(sys.argv) > 1 and sys.argv[1] == "--create-examples":
        # Create examples and exit
        temp_path = demonstrate_migration()
        print(f"\n✅ Examples created in: {temp_path}")
        return

    print("🚀 Nicestlog Migration Examples Demo")
    print("=" * 50)
    print()
    print("This demo shows:")
    print("• Real before/after migration examples")
    print("• Different logging library migration paths")
    print("• Practical commands you can run")
    print()

    # Show the examples
    demonstrate_migration()

    # Show library comparison
    show_library_comparison()

    print("\n🎯 Next Steps:")
    print("   1. Try: nicestlog demo basic")
    print("   2. Analyze your project: nicestlog migrate /path/to/your/project")
    print(
        "   3. Apply migration: nicestlog migrate /path/to/your/project --do-migrate --backup"
    )
    print("   4. Validate: nicestlog check /path/to/your/project")


if __name__ == "__main__":
    main()
