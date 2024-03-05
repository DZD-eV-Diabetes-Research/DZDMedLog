/**
 * MedLog REST API
 * No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)
 *
 * The version of the OpenAPI document: 0.0.1
 * 
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 *
 */

(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD.
    define(['expect.js', process.cwd()+'/src/index'], factory);
  } else if (typeof module === 'object' && module.exports) {
    // CommonJS-like environments that support module.exports, like Node.
    factory(require('expect.js'), require(process.cwd()+'/src/index'));
  } else {
    // Browser globals (root is window)
    factory(root.expect, root.MedLogRestApi);
  }
}(this, function(expect, MedLogRestApi) {
  'use strict';

  var instance;

  beforeEach(function() {
    instance = new MedLogRestApi.Intake();
  });

  var getProperty = function(object, getter, property) {
    // Use getter method if present; otherwise, get the property directly.
    if (typeof object[getter] === 'function')
      return object[getter]();
    else
      return object[property];
  }

  var setProperty = function(object, setter, property, value) {
    // Use setter method if present; otherwise, set the property directly.
    if (typeof object[setter] === 'function')
      object[setter](value);
    else
      object[property] = value;
  }

  describe('Intake', function() {
    it('should create an instance of Intake', function() {
      // uncomment below and update the code to test Intake
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be.a(MedLogRestApi.Intake);
    });

    it('should have the property createdAt (base name: "created_at")', function() {
      // uncomment below and update the code to test the property createdAt
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

    it('should have the property id (base name: "id")', function() {
      // uncomment below and update the code to test the property id
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

    it('should have the property interviewId (base name: "interview_id")', function() {
      // uncomment below and update the code to test the property interviewId
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

    it('should have the property pharmazentralnummer (base name: "pharmazentralnummer")', function() {
      // uncomment below and update the code to test the property pharmazentralnummer
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

    it('should have the property intakeStartTimeUtc (base name: "intake_start_time_utc")', function() {
      // uncomment below and update the code to test the property intakeStartTimeUtc
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

    it('should have the property intakeEndTimeUtc (base name: "intake_end_time_utc")', function() {
      // uncomment below and update the code to test the property intakeEndTimeUtc
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

    it('should have the property administeredByDoctor (base name: "administered_by_doctor")', function() {
      // uncomment below and update the code to test the property administeredByDoctor
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

    it('should have the property intakeRegularOrAsNeeded (base name: "intake_regular_or_as_needed")', function() {
      // uncomment below and update the code to test the property intakeRegularOrAsNeeded
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

    it('should have the property dosePerDay (base name: "dose_per_day")', function() {
      // uncomment below and update the code to test the property dosePerDay
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

    it('should have the property regularIntervallOfDailyDose (base name: "regular_intervall_of_daily_dose")', function() {
      // uncomment below and update the code to test the property regularIntervallOfDailyDose
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

    it('should have the property asNeededDoseUnit (base name: "as_needed_dose_unit")', function() {
      // uncomment below and update the code to test the property asNeededDoseUnit
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

    it('should have the property consumedMedsToday (base name: "consumed_meds_today")', function() {
      // uncomment below and update the code to test the property consumedMedsToday
      //var instance = new MedLogRestApi.Intake();
      //expect(instance).to.be();
    });

  });

}));
