Feature: User Authentication
  As a VaultMind user
  I want to log in to the application
  So that I can access my knowledge base

  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter valid credentials
    Then I should be redirected to the dashboard

  Scenario: Failed login with invalid credentials
    Given I am on the login page
    When I enter invalid credentials
    Then I should see an error message
