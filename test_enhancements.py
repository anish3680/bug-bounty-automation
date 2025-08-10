#!/usr/bin/env python3
"""
Test Script for Bug Bounty Automation Framework v3.1
Validates all Phase 1 enhancements
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
import tempfile
import sys

class FrameworkTester:
    def __init__(self):
        self.framework_dir = Path(__file__).parent
        self.test_results = {}
        self.passed_tests = 0
        self.failed_tests = 0

    def run_test(self, test_name: str, test_func):
        """Run a test and record results"""
        print(f"\n🧪 Testing: {test_name}")
        print("=" * 60)
        
        try:
            result = test_func()
            if result:
                print(f"✅ PASSED: {test_name}")
                self.test_results[test_name] = "PASSED"
                self.passed_tests += 1
            else:
                print(f"❌ FAILED: {test_name}")
                self.test_results[test_name] = "FAILED"
                self.failed_tests += 1
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {e}")
            self.test_results[test_name] = f"ERROR: {e}"
            self.failed_tests += 1

    def test_enhanced_email_system(self):
        """Test enhanced email system with graceful fallbacks"""
        print("   📧 Testing email system...")
        
        try:
            # Test loading non-existent config (should not crash)
            from send_email import load_email_config
            
            config = load_email_config('non_existent_config.json')
            if config is None:
                print("   ✅ Graceful fallback for missing config works")
                return True
            else:
                print("   ❌ Should return None for missing config")
                return False
                
        except Exception as e:
            print(f"   ❌ Email test failed: {e}")
            return False

    def test_tool_health_checker(self):
        """Test enhanced tool health checker"""
        print("   🔧 Testing tool health checker...")
        
        try:
            # Test tool health checker import and basic functionality
            from tool_health_checker import ToolHealthChecker
            
            checker = ToolHealthChecker()
            status = checker.get_comprehensive_status()
            
            if isinstance(status, dict) and len(status) > 0:
                print(f"   ✅ Tool status retrieved: {len(status)} tools checked")
                
                # Check if required tools are identified
                required_tools = [name for name, info in status.items() if info.get('required')]
                print(f"   ✅ Required tools identified: {len(required_tools)}")
                
                return True
            else:
                print("   ❌ Tool status check failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Tool health checker test failed: {e}")
            return False

    def test_ai_model_installer(self):
        """Test AI model installer"""
        print("   🤖 Testing AI model installer...")
        
        try:
            from ai_model_installer import AIModelInstaller
            
            installer = AIModelInstaller()
            
            # Test Ollama status check
            running, status = installer.check_ollama_status()
            print(f"   ℹ️  Ollama status: {status}")
            
            # Test system resource detection
            resources = installer.get_system_resources()
            if 'memory_available_gb' in resources and 'disk_free_gb' in resources:
                print("   ✅ System resources detected successfully")
                
                # Test model recommendations
                recommendations = installer.recommend_models_for_system()
                if isinstance(recommendations, list):
                    print(f"   ✅ Model recommendations generated: {len(recommendations)} models")
                    return True
            
            return False
                
        except Exception as e:
            print(f"   ❌ AI model installer test failed: {e}")
            return False

    def test_false_positive_filter(self):
        """Test AI false positive filter"""
        print("   🎯 Testing false positive filter...")
        
        try:
            from ai_false_positive_filter import AIFalsePositiveFilter, VulnerabilityFindings
            
            fp_filter = AIFalsePositiveFilter()
            
            # Create test finding
            test_finding = VulnerabilityFindings(
                id="test_1",
                type="xss",
                severity="medium",
                url="https://test.example.com/page.php",
                title="Test XSS",
                description="Test XSS vulnerability",
                evidence="<script>alert('test')</script>",
                source_tool="nuclei"
            )
            
            # Test pattern-based FP detection
            is_fp, reason = fp_filter.check_pattern_based_fp(test_finding)
            print(f"   ℹ️  Pattern-based FP check: {is_fp} - {reason}")
            
            # Test context analysis
            context_fp, context_reason = fp_filter._analyze_context(test_finding)
            print(f"   ℹ️  Context analysis: {context_fp} - {context_reason}")
            
            print("   ✅ False positive filter working")
            return True
                
        except Exception as e:
            print(f"   ❌ False positive filter test failed: {e}")
            return False

    def test_enhanced_report_generator(self):
        """Test enhanced report generator"""
        print("   📝 Testing enhanced report generator...")
        
        try:
            from enhanced_report_generator import EnhancedReportGenerator
            
            generator = EnhancedReportGenerator()
            
            # Test vulnerability type mappings
            vuln_mappings = generator.vuln_type_mapping
            if 'xss' in vuln_mappings and 'sqli' in vuln_mappings:
                print("   ✅ Vulnerability type mappings loaded")
            
            # Test platform templates
            platforms = generator.platform_templates
            if 'hackerone' in platforms and 'bugcrowd' in platforms:
                print("   ✅ Platform templates available")
            
            # Test CVSS score calculation
            score = generator._calculate_cvss_score('high')
            if isinstance(score, (int, float)) and 0 <= score <= 10:
                print(f"   ✅ CVSS calculation working: High = {score}")
                return True
            
            return False
                
        except Exception as e:
            print(f"   ❌ Enhanced report generator test failed: {e}")
            return False

    def test_smart_updater(self):
        """Test smart updater system"""
        print("   🔄 Testing smart updater...")
        
        try:
            from smart_updater import SmartUpdater
            
            updater = SmartUpdater()
            
            # Test component configuration
            components = updater.components
            if 'nuclei_templates' in components and 'go_tools' in components:
                print("   ✅ Update components configured")
            
            # Test health report generation
            health = updater.get_system_health()
            if 'timestamp' in health and 'overall_score' in health:
                print(f"   ✅ System health report generated: {health['overall_score']:.1f}%")
                return True
            
            return False
                
        except Exception as e:
            print(f"   ❌ Smart updater test failed: {e}")
            return False

    def test_main_scanner_integration(self):
        """Test main scanner integration"""
        print("   🎯 Testing main scanner integration...")
        
        try:
            # Test that all imports work
            from bug_bounty_scanner import BugBountyFramework
            
            # Try to initialize framework
            framework = BugBountyFramework()
            
            if hasattr(framework, 'version') and framework.version:
                print(f"   ✅ Framework initialized: v{framework.version}")
                
                # Test banner generation
                if hasattr(framework, 'banner') and framework.banner:
                    print("   ✅ Banner generation working")
                    return True
            
            return False
                
        except Exception as e:
            print(f"   ❌ Main scanner integration test failed: {e}")
            return False

    def test_configuration_files(self):
        """Test configuration file handling"""
        print("   ⚙️ Testing configuration files...")
        
        try:
            config_dir = self.framework_dir / 'config'
            
            # Check if config directory exists
            if not config_dir.exists():
                config_dir.mkdir(exist_ok=True)
                print("   ✅ Config directory created")
            
            # Test email config loading
            email_config_file = config_dir / 'email_config.json'
            if email_config_file.exists():
                with open(email_config_file, 'r') as f:
                    config = json.load(f)
                    if isinstance(config, dict):
                        print("   ✅ Email config loaded successfully")
                        return True
            else:
                print("   ℹ️  Email config not found (optional)")
                return True
                
        except Exception as e:
            print(f"   ❌ Configuration files test failed: {e}")
            return False

    async def test_async_functionality(self):
        """Test async functionality"""
        print("   ⚡ Testing async functionality...")
        
        try:
            # Test async report generation
            from enhanced_report_generator import EnhancedReportGenerator
            
            generator = EnhancedReportGenerator()
            
            test_vuln = {
                'type': 'xss',
                'url': 'https://test.example.com',
                'severity': 'medium',
                'evidence': 'Test evidence'
            }
            
            # Test AI enhancement (should gracefully handle unavailable AI)
            enhanced_report = await generator.ai_enhance_report(test_vuln)
            
            if hasattr(enhanced_report, 'title') and hasattr(enhanced_report, 'severity'):
                print("   ✅ Async report generation working")
                return True
            
            return False
                
        except Exception as e:
            print(f"   ❌ Async functionality test failed: {e}")
            return False

    def run_file_permissions_test(self):
        """Test file permissions for executable scripts"""
        print("   🔐 Testing file permissions...")
        
        executable_files = [
            'bug_bounty_scanner.py',
            'tool_health_checker.py',
            'ai_model_installer.py',
            'ai_false_positive_filter.py',
            'enhanced_report_generator.py',
            'smart_updater.py'
        ]
        
        all_executable = True
        for file_name in executable_files:
            file_path = self.framework_dir / file_name
            if file_path.exists() and os.access(file_path, os.X_OK):
                print(f"   ✅ {file_name} is executable")
            else:
                print(f"   ❌ {file_name} is not executable")
                all_executable = False
        
        return all_executable

    def test_requirements_file(self):
        """Test requirements.txt completeness"""
        print("   📋 Testing requirements file...")
        
        try:
            requirements_file = self.framework_dir / 'requirements.txt'
            
            if requirements_file.exists():
                with open(requirements_file, 'r') as f:
                    content = f.read()
                    
                # Check for essential packages
                essential_packages = ['requests', 'aiohttp', 'asyncio-compat']
                missing_packages = []
                
                for package in essential_packages:
                    if package not in content:
                        missing_packages.append(package)
                
                if not missing_packages:
                    print("   ✅ Requirements file contains essential packages")
                    return True
                else:
                    print(f"   ❌ Missing packages: {missing_packages}")
                    return False
            else:
                print("   ❌ Requirements file not found")
                return False
                
        except Exception as e:
            print(f"   ❌ Requirements test failed: {e}")
            return False

    def generate_test_report(self):
        """Generate comprehensive test report"""
        
        print("\n" + "="*80)
        print("🧪 COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        print(f"\n📊 Test Summary:")
        print(f"   ✅ Passed: {self.passed_tests}")
        print(f"   ❌ Failed: {self.failed_tests}")
        print(f"   📈 Success Rate: {(self.passed_tests/(self.passed_tests + self.failed_tests)*100):.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status_emoji = "✅" if result == "PASSED" else "❌"
            print(f"   {status_emoji} {test_name}: {result}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if self.failed_tests == 0:
            print("   🎉 All tests passed! Framework is ready for use.")
        elif self.failed_tests < 3:
            print("   ⚠️  Minor issues detected. Framework is mostly functional.")
        else:
            print("   ⚠️  Multiple issues detected. Please review failed tests.")
        
        print(f"\n🚀 Next Steps:")
        if self.failed_tests == 0:
            print("   1. Run a test scan: python3 bug_bounty_scanner.py scan example.com")
            print("   2. Configure email settings if needed")
            print("   3. Install AI models for enhanced analysis")
        else:
            print("   1. Review and fix failed tests")
            print("   2. Re-run test suite")
            print("   3. Check logs for additional details")

    async def run_all_tests(self):
        """Run all tests"""
        
        print("🚀 Bug Bounty Automation Framework v3.1 - Test Suite")
        print("="*80)
        
        # Test basic functionality
        self.run_test("Enhanced Email System", self.test_enhanced_email_system)
        self.run_test("Tool Health Checker", self.test_tool_health_checker)
        self.run_test("AI Model Installer", self.test_ai_model_installer)
        self.run_test("False Positive Filter", self.test_false_positive_filter)
        self.run_test("Enhanced Report Generator", self.test_enhanced_report_generator)
        self.run_test("Smart Updater", self.test_smart_updater)
        self.run_test("Main Scanner Integration", self.test_main_scanner_integration)
        self.run_test("Configuration Files", self.test_configuration_files)
        self.run_test("File Permissions", self.run_file_permissions_test)
        self.run_test("Requirements File", self.test_requirements_file)
        
        # Test async functionality
        print(f"\n🧪 Testing: Async Functionality")
        print("=" * 60)
        try:
            result = await self.test_async_functionality()
            if result:
                print(f"✅ PASSED: Async Functionality")
                self.test_results["Async Functionality"] = "PASSED"
                self.passed_tests += 1
            else:
                print(f"❌ FAILED: Async Functionality")
                self.test_results["Async Functionality"] = "FAILED"
                self.failed_tests += 1
        except Exception as e:
            print(f"❌ ERROR: Async Functionality - {e}")
            self.test_results["Async Functionality"] = f"ERROR: {e}"
            self.failed_tests += 1
        
        # Generate final report
        self.generate_test_report()

async def main():
    """Main test execution"""
    tester = FrameworkTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
