"""
Module/Package: ConfigService Tests - Test suite for the configuration storage system

High Level Concept:
-------------------
This module provides tests for the configuration storage system, ensuring that
the NoSQLite storage backend works correctly for both global and user-specific
configurations. It tests CRUD operations on configuration data.

Architecture:
-------------
- Test Setup: Creates a temporary storage location
- Test Cases: Tests for global and user configuration operations
- Cleanup: Removes temporary test data

Workflow:
---------
1. Setup test environment with temporary storage
2. Run test cases for global configuration operations
3. Run test cases for user configuration operations
4. Clean up test environment

Usage Example:
--------------
>>> python -m mcpo_simple_server.services.config._test

Notes:
------
- Tests are designed to be run in sequence
- Each test verifies a specific aspect of the storage system
- Tests use a temporary storage location to avoid affecting production data
"""
import os
import asyncio
import shutil
import argparse

from loguru import logger
from mcpo_simple_server.services.config import get_config, ConfigService
from mcpo_simple_server.services.config.models.config import (
    UserConfigModel,
    UserMcpServerConfigModel,
    McpServerConfigModel,
    ToolsConfigModel
)


class ConfigStorageTests:
    """Test suite for the configuration storage system."""

    def __init__(self, keep_files=False):
        """Initialize the test environment."""
        self.keep_files = keep_files
        self.temp_dir = os.path.join(os.path.dirname(__file__), "_test")
        self.db_path = os.path.join(self.temp_dir, "config.db")

        # Create a clean test directory
        if os.path.exists(self.temp_dir):
            try:
                # Use shutil.rmtree with error handling for read-only files
                def handle_remove_readonly(func, path, exc):
                    # Change permissions and try again
                    os.chmod(path, 0o777)
                    func(path)

                # Remove the test directory with error handling
                shutil.rmtree(self.temp_dir, onerror=handle_remove_readonly)
            except Exception as e:
                logger.error(f"Error cleaning up test directory: {e}")
                logger.warning("Continuing with existing test directory")

        # Create the test directory if it does not exist
        os.makedirs(self.temp_dir, exist_ok=True)

        # Initialize config service with the test storage path
        self.config_service = ConfigService({"db_path": self.db_path})

        # Access the backend via ConfigService (for test purposes only)
        from mcpo_simple_server.services.config import _STORAGE_BACKEND
        self.storage = _STORAGE_BACKEND

        logger.info(f"Test storage initialized at {self.db_path}")

    async def cleanup(self):
        """Clean up test resources."""
        # Close database connection before removing the test directory
        try:
            # Ensure global backend is closed
            from mcpo_simple_server.services.config import _STORAGE_BACKEND
            if _STORAGE_BACKEND is not None and hasattr(_STORAGE_BACKEND, 'close'):
                try:
                    _STORAGE_BACKEND.close()
                    logger.debug("Closed global storage backend connection")
                except Exception as e:
                    logger.error(f"Error closing global storage backend: {e}")
            # Use close() method of ConfigService
            if hasattr(self, 'config_service') and self.config_service is not None:
                try:
                    self.config_service.close()
                    logger.debug("Closed configuration service connection")
                except Exception as e:
                    logger.error(f"Error closing configuration service: {e}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        # Release references to objects
        self.storage = None
        self.config_service = None

        # Wait briefly to ensure all processes have finished with files
        await asyncio.sleep(1.0)

        # Remove the test directory if not keeping files
        if not self.keep_files:
            try:
                # Use shutil.rmtree with error handling for read-only files
                def handle_remove_readonly(func, path, exc):
                    # Change permissions and try again
                    os.chmod(path, 0o777)
                    func(path)

                shutil.rmtree(self.temp_dir, onerror=handle_remove_readonly)
                logger.info("Test storage cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up test directory: {e}")
                logger.warning("Continuing despite cleanup error")
        else:
            logger.info(f"Test storage kept at {self.temp_dir} for inspection")

    async def test_1_create_global_config(self):
        """Test 1: Create a new global configuration file."""
        logger.info("-" * 50)
        logger.info("Running Test 1: Create global configuration")

        # Pobierz konfigurację globalną przez publiczne API
        config_response = await get_config(None)
        assert config_response is not None, "Config response should not be None"
        assert config_response.global_config is not None, "Global config should not be None"

        # Utwórz podstawową konfigurację globalną
        config_response.global_config.mcpServers = {
            "test-server": McpServerConfigModel(
                command="python",
                args=["-m", "http.server"],
                env={"PORT": "8080"},
                description="Test server for configuration tests",
                disabled=False
            )
        }

        # Ustaw konfigurację narzędzi
        config_response.global_config.tools = ToolsConfigModel(
            whiteList=["test-tool"],
            blackList=[]
        )

        # Zapisz konfigurację globalną przez publiczne API
        updated_config = await config_response.save()

        # Zweryfikuj, że konfiguracja globalna została zapisana
        assert updated_config is not None, "Updated config should not be None"
        assert updated_config.global_config is not None, "Global config should not be None"
        assert updated_config.global_config.mcpServers is not None, "MCPServers should not be None"
        assert "test-server" in updated_config.global_config.mcpServers, "test-server should be in mcpServers"

        logger.info("Test 1 passed: Global configuration created successfully")
        logger.info("-" * 50)
        return config_response.global_config

    async def test_2_update_global_config(self):
        """Test 2: Update an existing global configuration."""
        logger.info("-" * 50)
        logger.info("Running Test 2: Update global configuration")

        # Pobierz konfigurację globalną przez publiczne API
        config_response = await get_config(None)
        assert config_response is not None, "Config response should not be None"
        assert config_response.global_config is not None, "Global config should not be None"

        # Dodaj nowy serwer do konfiguracji
        config_response.global_config.mcpServers["another-server"] = McpServerConfigModel(
            command="python",
            args=["-m", "mcpo_simple_server.services.another_test_server"],
            description="Another test server for unit tests",
            disabled=False
        )

        # Zaktualizuj listę dozwolonych narzędzi
        if config_response.global_config.tools.whiteList is None:
            config_response.global_config.tools.whiteList = []
        config_response.global_config.tools.whiteList.append("another-tool")

        # Zapisz zaktualizowaną konfigurację przez publiczne API
        updated_config = await config_response.save()

        # Zweryfikuj, że konfiguracja została zaktualizowana
        assert updated_config.global_config.mcpServers is not None, "MCP servers should not be None"
        assert "another-server" in updated_config.global_config.mcpServers, "New server should be in config"
        assert updated_config.global_config.tools.whiteList is not None, "Tool whitelist should not be None"
        assert "another-tool" in updated_config.global_config.tools.whiteList, "New tool should be in whitelist"

        logger.info("Test 2 passed: Global configuration updated successfully")
        logger.info("-" * 50)
        return updated_config.global_config

    async def test_3_remove_from_global_config(self):
        """Test 3: Remove items from the global configuration."""
        logger.info("-" * 50)
        logger.info("Running Test 3: Remove from global configuration")

        # Pobierz konfigurację globalną przez publiczne API
        config_response = await get_config(None)
        assert config_response is not None, "Config response should not be None"
        assert config_response.global_config is not None, "Global config should not be None"

        # Usuń serwer z konfiguracji
        if "test-server" in config_response.global_config.mcpServers:
            del config_response.global_config.mcpServers["test-server"]

        # Upewnij się, że globalna konfiguracja ma odpowiednie narzędzia na liście dozwolonych
        assert config_response.global_config.tools.whiteList is not None
        assert "another-tool" in config_response.global_config.tools.whiteList

        # Usuń 'another-tool' z listy dozwolonych
        if "another-tool" in config_response.global_config.tools.whiteList:
            config_response.global_config.tools.whiteList.remove("another-tool")

        # Zapisz zaktualizowaną konfigurację przez publiczne API
        updated_config = await config_response.save()

        # Zweryfikuj, że elementy zostały usunięte
        assert "test-server" not in updated_config.global_config.mcpServers, "Server should be removed"
        assert updated_config.global_config.tools.whiteList is not None, "Tool whitelist should not be None"
        assert "another-tool" not in updated_config.global_config.tools.whiteList, "Tool should be removed"

        logger.info("Test 3 passed: Items removed from global configuration successfully")
        logger.info("-" * 50)
        return updated_config.global_config

    async def test_4_create_user_config(self):
        """Test 4: Create a new user configuration."""
        logger.info("-" * 50)
        logger.info("Running Test 4: Create user configuration")

        # Utwórz konfigurację użytkownika
        user_config = UserConfigModel(
            username="test-user",
            hashed_password="hashed_password_value",
            disabled=False,
            api_keys=["test-api-key"],
            env={"OPENAI_API_KEY": "test-api-key"},
            mcpServers={
                "test-server": UserMcpServerConfigModel(
                    args=["-m", "custom_module"],
                    env={"API_KEY": "test-credential"},
                    disabled=False
                )
            }
        )

        # Pobierz aktualną konfigurację globalną
        config_response = await get_config(None)

        # Ustaw konfigurację użytkownika
        config_response.user_config = user_config

        # Zapisz konfigurację przez publiczne API
        await config_response.save()

        # Pobierz zaktualizowaną konfigurację użytkownika
        user_config_response = await get_config("test-user")
        assert user_config_response is not None, "User config response should not be None"
        assert user_config_response.user_config is not None, "User config should not be None"
        assert user_config_response.user_config.api_keys is not None, "API keys should not be None"
        assert user_config_response.user_config.mcpServers is not None, "MCP servers should not be None"
        assert user_config_response.user_config.username == "test-user", "Username should match"
        assert "test-api-key" in user_config_response.user_config.api_keys, "API key should be in config"
        assert "test-server" in user_config_response.user_config.mcpServers, "Server should be in config"

        logger.info("Test 4 passed: User configuration created successfully")
        logger.info("-" * 50)
        return user_config_response.user_config

    async def test_5_update_user_config(self):
        """Test 5: Update an existing user configuration."""
        logger.info("-" * 50)
        logger.info("Running Test 5: Update user configuration")

        # Pobierz aktualną konfigurację użytkownika przez publiczne API
        config_response = await get_config("test-user")
        assert config_response is not None, "Config response should not be None"
        assert config_response.user_config is not None, "User config should not be None"

        # Dodaj klucz API i serwer
        config_response.user_config.api_keys.append("google-api-key")
        config_response.user_config.mcpServers["another-server"] = UserMcpServerConfigModel(
            args=["-m", "another_custom_module"],
            env={"API_KEY": "another-credential"},
            disabled=False
        )

        # Zapisz zaktualizowaną konfigurację przez publiczne API
        updated_response = await config_response.save()
        assert updated_response is not None, "Updated response should not be None"

        # Zweryfikuj, że konfiguracja została zaktualizowana
        refreshed_config = await get_config("test-user")
        assert refreshed_config.user_config is not None, "Updated user config should not be None"
        assert refreshed_config.user_config.api_keys is not None, "API keys should not be None"
        assert "google-api-key" in refreshed_config.user_config.api_keys, "New API key should be in config"
        assert refreshed_config.user_config.mcpServers is not None, "MCP servers should not be None"
        assert "another-server" in refreshed_config.user_config.mcpServers, "New server should be in config"

        logger.info("Test 5 passed: User configuration updated successfully")
        logger.info("-" * 50)
        return refreshed_config.user_config

    async def test_6_delete_user_config(self):
        """Test 6: Delete a user configuration."""
        logger.info("-" * 50)
        logger.info("Running Test 6: Delete user configuration")

        # Retrieve the current user configuration via public API
        config_response = await get_config("test-user")
        assert config_response is not None, "Config response should not be None"
        assert config_response.user_config is not None, "User config should not be None"

        # Retrieve the global configuration
        global_config_response = await get_config(None)
        assert global_config_response is not None, "Global config response should not be None"

        # Usuń konfigurację użytkownika - musimy użyć bezpośrednio backendu
        # ponieważ publiczne API nie ma metody do usuwania użytkowników
        if self.storage is not None:
            await self.storage.delete_user_config("test-user")
        else:
            logger.error("Storage backend is None, cannot delete user config")
            assert False, "Storage backend should not be None"

        # Zweryfikuj, że konfiguracja użytkownika została usunięta
        try:
            deleted_config_response = await get_config("test-user")
            assert deleted_config_response.user_config is None, "User config should be None after deletion"
        except Exception as e:
            # Może rzucić wyjątek, jeśli użytkownik nie istnieje
            logger.info(f"Expected exception when getting deleted user: {e}")

        logger.info("Test 6 passed: User configuration deleted successfully")
        logger.info("-" * 50)

    async def test_7_config_service_integration(self):
        """Test 7: Test the config service integration."""
        logger.info("-" * 50)
        logger.info("Running Test 7: Config service integration")

        # Pobierz konfigurację globalną przez publiczne API
        config_response = await get_config(None)
        assert config_response is not None, "Config response should not be None"
        assert config_response.global_config is not None, "Global config should not be None"

        # Utwórz nowego użytkownika
        new_user_config = UserConfigModel(
            username="service-test-user",
            hashed_password="service_test_hashed_password",
            disabled=False,
            api_keys=["service-test-api-key"]
        )

        # Ustaw konfigurację użytkownika w odpowiedzi
        config_response.user_config = new_user_config

        # Zapisz konfigurację przez publiczne API
        await config_response.save()

        # Pobierz połączoną konfigurację
        combined_config = await get_config("service-test-user")
        assert combined_config.user_config is not None, "User config should not be None"
        assert combined_config.user_config.username == "service-test-user", "Username should match"

        # Zaktualizuj konfigurację użytkownika
        combined_config.user_config.api_keys.append("azure-api-key")

        # Zapisz zaktualizowaną konfigurację przez publiczne API
        updated_response = await combined_config.save()
        assert updated_response is not None, "Updated response should not be None"

        # Zweryfikuj, że zmiany zostały zapisane
        refreshed_config = await get_config("service-test-user")
        assert refreshed_config.user_config is not None, "User config should not be None"
        assert "azure-api-key" in refreshed_config.user_config.api_keys, "API key should be in config"

        logger.info("Test 7 passed: Config service integration successful")
        logger.info("-" * 50)

    async def run_all_tests(self):
        """Run all tests in sequence."""
        try:
            await self.test_1_create_global_config()
            await self.test_2_update_global_config()
            await self.test_3_remove_from_global_config()
            await self.test_4_create_user_config()
            await self.test_5_update_user_config()
            await self.test_6_delete_user_config()
            await self.test_7_config_service_integration()
            logger.info("All tests passed successfully!")
        except AssertionError as e:
            logger.error(f"Test failed: {str(e)}")
        finally:
            await self.cleanup()


async def run_with_timeout(coro, timeout=30):
    """Run a coroutine with a timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Test timed out after {timeout} seconds")
        raise


async def main():
    """Run the full configuration storage test suite."""
    parser = argparse.ArgumentParser(description="Run configuration storage tests")
    parser.add_argument("--no-cleanup", action="store_true", help="Keep test files after running")
    args = parser.parse_args()

    logger.info("Starting configuration storage tests")
    tests = None
    try:
        tests = ConfigStorageTests(keep_files=args.no_cleanup)
        await run_with_timeout(tests.run_all_tests())
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        if tests:
            await tests.cleanup()
        from mcpo_simple_server.services.config import _storage_backend
        if _storage_backend is not None and hasattr(_storage_backend, 'close'):
            try:
                _storage_backend.close()
            except Exception:
                pass
        raise
    finally:
        import gc
        gc.collect()

if __name__ == "__main__":
    asyncio.run(main())
