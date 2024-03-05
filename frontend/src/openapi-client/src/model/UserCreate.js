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
import DisplayName1 from './DisplayName1';
import Email from './Email';
import Id from './Id';

/**
 * The UserCreate model module.
 * @module model/UserCreate
 * @version 0.0.1
 */
class UserCreate {
    /**
     * Constructs a new <code>UserCreate</code>.
     * @alias module:model/UserCreate
     * @param id {module:model/Id} 
     */
    constructor(id) { 
        
        UserCreate.initialize(this, id);
    }

    /**
     * Initializes the fields of this object.
     * This method is used by the constructors of any subclasses, in order to implement multiple inheritance (mix-ins).
     * Only for internal use.
     */
    static initialize(obj, id) { 
        obj['id'] = id;
    }

    /**
     * Constructs a <code>UserCreate</code> from a plain JavaScript object, optionally creating a new instance.
     * Copies all relevant properties from <code>data</code> to <code>obj</code> if supplied or a new instance if not.
     * @param {Object} data The plain JavaScript object bearing properties of interest.
     * @param {module:model/UserCreate} obj Optional instance to populate.
     * @return {module:model/UserCreate} The populated <code>UserCreate</code> instance.
     */
    static constructFromObject(data, obj) {
        if (data) {
            obj = obj || new UserCreate();

            if (data.hasOwnProperty('email')) {
                obj['email'] = Email.constructFromObject(data['email']);
            }
            if (data.hasOwnProperty('display_name')) {
                obj['display_name'] = DisplayName1.constructFromObject(data['display_name']);
            }
            if (data.hasOwnProperty('user_name')) {
                obj['user_name'] = ApiClient.convertToType(data['user_name'], 'String');
            }
            if (data.hasOwnProperty('id')) {
                obj['id'] = Id.constructFromObject(data['id']);
            }
        }
        return obj;
    }

    /**
     * Validates the JSON data with respect to <code>UserCreate</code>.
     * @param {Object} data The plain JavaScript object bearing properties of interest.
     * @return {boolean} to indicate whether the JSON data is valid with respect to <code>UserCreate</code>.
     */
    static validateJSON(data) {
        // check to make sure all required properties are present in the JSON string
        for (const property of UserCreate.RequiredProperties) {
            if (!data.hasOwnProperty(property)) {
                throw new Error("The required field `" + property + "` is not found in the JSON data: " + JSON.stringify(data));
            }
        }
        // validate the optional field `email`
        if (data['email']) { // data not null
          Email.validateJSON(data['email']);
        }
        // validate the optional field `display_name`
        if (data['display_name']) { // data not null
          DisplayName1.validateJSON(data['display_name']);
        }
        // ensure the json data is a string
        if (data['user_name'] && !(typeof data['user_name'] === 'string' || data['user_name'] instanceof String)) {
            throw new Error("Expected the field `user_name` to be a primitive type in the JSON string but got " + data['user_name']);
        }
        // validate the optional field `id`
        if (data['id']) { // data not null
          Id.validateJSON(data['id']);
        }

        return true;
    }


}

UserCreate.RequiredProperties = ["id"];

/**
 * @member {module:model/Email} email
 */
UserCreate.prototype['email'] = undefined;

/**
 * @member {module:model/DisplayName1} display_name
 */
UserCreate.prototype['display_name'] = undefined;

/**
 * @member {String} user_name
 */
UserCreate.prototype['user_name'] = undefined;

/**
 * @member {module:model/Id} id
 */
UserCreate.prototype['id'] = undefined;






export default UserCreate;

