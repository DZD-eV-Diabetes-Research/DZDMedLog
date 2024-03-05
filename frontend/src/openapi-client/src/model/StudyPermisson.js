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

import ApiClient from '../ApiClient';

/**
 * The StudyPermisson model module.
 * @module model/StudyPermisson
 * @version 0.0.1
 */
class StudyPermisson {
    /**
     * Constructs a new <code>StudyPermisson</code>.
     * @alias module:model/StudyPermisson
     * @param studyId {String} 
     * @param userId {String} 
     */
    constructor(studyId, userId) { 
        
        StudyPermisson.initialize(this, studyId, userId);
    }

    /**
     * Initializes the fields of this object.
     * This method is used by the constructors of any subclasses, in order to implement multiple inheritance (mix-ins).
     * Only for internal use.
     */
    static initialize(obj, studyId, userId) { 
        obj['study_id'] = studyId;
        obj['user_id'] = userId;
    }

    /**
     * Constructs a <code>StudyPermisson</code> from a plain JavaScript object, optionally creating a new instance.
     * Copies all relevant properties from <code>data</code> to <code>obj</code> if supplied or a new instance if not.
     * @param {Object} data The plain JavaScript object bearing properties of interest.
     * @param {module:model/StudyPermisson} obj Optional instance to populate.
     * @return {module:model/StudyPermisson} The populated <code>StudyPermisson</code> instance.
     */
    static constructFromObject(data, obj) {
        if (data) {
            obj = obj || new StudyPermisson();

            if (data.hasOwnProperty('created_at')) {
                obj['created_at'] = ApiClient.convertToType(data['created_at'], 'Date');
            }
            if (data.hasOwnProperty('is_study_viewer')) {
                obj['is_study_viewer'] = ApiClient.convertToType(data['is_study_viewer'], 'Boolean');
            }
            if (data.hasOwnProperty('is_study_interviewer')) {
                obj['is_study_interviewer'] = ApiClient.convertToType(data['is_study_interviewer'], 'Boolean');
            }
            if (data.hasOwnProperty('is_study_admin')) {
                obj['is_study_admin'] = ApiClient.convertToType(data['is_study_admin'], 'Boolean');
            }
            if (data.hasOwnProperty('study_id')) {
                obj['study_id'] = ApiClient.convertToType(data['study_id'], 'String');
            }
            if (data.hasOwnProperty('user_id')) {
                obj['user_id'] = ApiClient.convertToType(data['user_id'], 'String');
            }
            if (data.hasOwnProperty('id')) {
                obj['id'] = ApiClient.convertToType(data['id'], 'String');
            }
        }
        return obj;
    }

    /**
     * Validates the JSON data with respect to <code>StudyPermisson</code>.
     * @param {Object} data The plain JavaScript object bearing properties of interest.
     * @return {boolean} to indicate whether the JSON data is valid with respect to <code>StudyPermisson</code>.
     */
    static validateJSON(data) {
        // check to make sure all required properties are present in the JSON string
        for (const property of StudyPermisson.RequiredProperties) {
            if (!data.hasOwnProperty(property)) {
                throw new Error("The required field `" + property + "` is not found in the JSON data: " + JSON.stringify(data));
            }
        }
        // ensure the json data is a string
        if (data['study_id'] && !(typeof data['study_id'] === 'string' || data['study_id'] instanceof String)) {
            throw new Error("Expected the field `study_id` to be a primitive type in the JSON string but got " + data['study_id']);
        }
        // ensure the json data is a string
        if (data['user_id'] && !(typeof data['user_id'] === 'string' || data['user_id'] instanceof String)) {
            throw new Error("Expected the field `user_id` to be a primitive type in the JSON string but got " + data['user_id']);
        }
        // ensure the json data is a string
        if (data['id'] && !(typeof data['id'] === 'string' || data['id'] instanceof String)) {
            throw new Error("Expected the field `id` to be a primitive type in the JSON string but got " + data['id']);
        }

        return true;
    }


}

StudyPermisson.RequiredProperties = ["study_id", "user_id"];

/**
 * @member {Date} created_at
 */
StudyPermisson.prototype['created_at'] = undefined;

/**
 * This is the minimal access to a study. The user can see all data but can not alter anything
 * @member {Boolean} is_study_viewer
 * @default true
 */
StudyPermisson.prototype['is_study_viewer'] = true;

/**
 * Study interviewers can create new interview entries for this study.
 * @member {Boolean} is_study_interviewer
 * @default false
 */
StudyPermisson.prototype['is_study_interviewer'] = false;

/**
 * Study admins can give access to the study to new users.
 * @member {Boolean} is_study_admin
 * @default false
 */
StudyPermisson.prototype['is_study_admin'] = false;

/**
 * @member {String} study_id
 */
StudyPermisson.prototype['study_id'] = undefined;

/**
 * @member {String} user_id
 */
StudyPermisson.prototype['user_id'] = undefined;

/**
 * @member {String} id
 */
StudyPermisson.prototype['id'] = undefined;






export default StudyPermisson;

