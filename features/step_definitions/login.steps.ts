import { Given, When, Then } from '@cucumber/cucumber';

Given('I am on the login page', function () {
  // Navigate to /login
});

When('I enter valid credentials', function () {
  // Fill in username and password with valid values
});

When('I enter invalid credentials', function () {
  // Fill in username and password with invalid values
});

Then('I should be redirected to the dashboard', function () {
  // Assert URL is /dashboard or similar
});

Then('I should see an error message', function () {
  // Assert error message is visible
});
