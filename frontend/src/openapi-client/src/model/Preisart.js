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
 * The Preisart model module.
 * @module model/Preisart
 * @version 0.0.1
 */
class Preisart {
    /**
     * Constructs a new <code>Preisart</code>.
     * @alias module:model/Preisart
     * @param preisart {String} preiart id
     * @param bedeutung {String} Bedeutung
     */
    constructor(preisart, bedeutung) { 
        
        Preisart.initialize(this, preisart, bedeutung);
    }

    /**
     * Initializes the fields of this object.
     * This method is used by the constructors of any subclasses, in order to implement multiple inheritance (mix-ins).
     * Only for internal use.
     */
    static initialize(obj, preisart, bedeutung) { 
        obj['preisart'] = preisart;
        obj['bedeutung'] = bedeutung;
    }

    /**
     * Constructs a <code>Preisart</code> from a plain JavaScript object, optionally creating a new instance.
     * Copies all relevant properties from <code>data</code> to <code>obj</code> if supplied or a new instance if not.
     * @param {Object} data The plain JavaScript object bearing properties of interest.
     * @param {module:model/Preisart} obj Optional instance to populate.
     * @return {module:model/Preisart} The populated <code>Preisart</code> instance.
     */
    static constructFromObject(data, obj) {
        if (data) {
            obj = obj || new Preisart();

            if (data.hasOwnProperty('created_at')) {
                obj['created_at'] = ApiClient.convertToType(data['created_at'], 'Date');
            }
            if (data.hasOwnProperty('preisart')) {
                obj['preisart'] = ApiClient.convertToType(data['preisart'], 'String');
            }
            if (data.hasOwnProperty('bedeutung')) {
                obj['bedeutung'] = ApiClient.convertToType(data['bedeutung'], 'String');
            }
        }
        return obj;
    }

    /**
     * Validates the JSON data with respect to <code>Preisart</code>.
     * @param {Object} data The plain JavaScript object bearing properties of interest.
     * @return {boolean} to indicate whether the JSON data is valid with respect to <code>Preisart</code>.
     */
    static validateJSON(data) {
        // check to make sure all required properties are present in the JSON string
        for (const property of Preisart.RequiredProperties) {
            if (!data.hasOwnProperty(property)) {
                throw new Error("The required field `" + property + "` is not found in the JSON data: " + JSON.stringify(data));
            }
        }
        // ensure the json data is a string
        if (data['preisart'] && !(typeof data['preisart'] === 'string' || data['preisart'] instanceof String)) {
            throw new Error("Expected the field `preisart` to be a primitive type in the JSON string but got " + data['preisart']);
        }
        // ensure the json data is a string
        if (data['bedeutung'] && !(typeof data['bedeutung'] === 'string' || data['bedeutung'] instanceof String)) {
            throw new Error("Expected the field `bedeutung` to be a primitive type in the JSON string but got " + data['bedeutung']);
        }

        return true;
    }


}

Preisart.RequiredProperties = ["preisart", "bedeutung"];

/**
 * @member {Date} created_at
 */
Preisart.prototype['created_at'] = undefined;

/**
 * preiart id
 * @member {String} preisart
 */
Preisart.prototype['preisart'] = undefined;

/**
 * Bedeutung
 * @member {String} bedeutung
 */
Preisart.prototype['bedeutung'] = undefined;






export default Preisart;

