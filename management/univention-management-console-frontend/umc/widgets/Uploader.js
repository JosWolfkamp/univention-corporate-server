/*
 * Copyright 2011-2012 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global define dojox*/


define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/when",
	"dojo/dom-class",
	"dojo/dom-style",
	"dojox/form/Uploader",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"umc/widgets/_FormWidgetMixin",
	"umc/i18n!umc/app",
	"dojox/form/uploader/plugins/IFrame"
], function(declare, lang, array, when, domClass, style, Uploader, tools, dialog, ContainerWidget, Button, _FormWidgetMixin, _) {
	return declare("umc.widgets.Uploader", [ ContainerWidget, _FormWidgetMixin ], {
		'class': 'umcUploader',

		// command: String
		//		The UMCP command to which the data shall be uploaded.
		//		If not given, the data is sent to umcp/upload which will return the
		//		file content encoded as base64.
		command: '',

		// dynamicOptions: Object?|Function?
		//		Reference to a dictionary containing options that are passed over to
		//		the upload command. Can be a function that is expected to return a
		//		dictionary.
		dynamicOptions: null,

		// buttonLabel: String
		//		The label that is displayed on the upload button.
		buttonLabel: 'Upload',

		// showClearButton: Boolean
		//		The clear button is shown only if this attribute is set to true.
		showClearButton: true,

		// clearButtonLabel: String
		//		The label that is displayed on the upload button.
		clearButtonLabel: 'Clear data',

		// displayErrorMessage: Boolean
		// 		Show message if error occured when uploading file.
		displayErrorMessage: true,

		// data: Object
		//		An object containing the file data that has been uploaded.
		data: null,

		// value: String
		//		The content of the base64 encoded file data.
		value: "",

		// maxSize: Number
		//		A size limit for the uploaded file.
		maxSize: 524288,

		// make sure that no sizeClass is being set
		sizeClass: null,

		// this form element should always be valid
		valid: true,

		// reference to the dojox/form/Uploader instance
		_uploader: null,

		// internal reference to 'clear' button
		_clearButton: null,

		// internal reference to the original user specified label
		_origButtonLabel: null,

		// internal flag that indicates that the data is being set
		_settingData: false,

		constructor: function() {
			this.buttonLabel = _('Upload');
			this.clearButtonLabel = _('Clear data');
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			// save the original label
			this._origButtonLabel = this.buttonLabel;
		},

		buildRendering: function() {
			this.inherited(arguments);

			// until Dojo2.0 "dojox.form.Uploader" must be used!
			this._uploader = new dojox.form.Uploader({
				url: '/umcp/upload' + (this.command ? '/' + this.command : ''),
				label: this.buttonLabel,
				getForm: function() {
					// make sure that the Uploader does not find any of our encapsulating forms
					return null;
				}
			});
			domClass.add(this._uploader.domNode, 'umcButton');
			this._uploader.set('iconClass', 'umcIconAdd');
			style.set(this._uploader.domNode, 'display', 'inline-block');
			this.addChild(this._uploader);

			if ( this.showClearButton ) {
				this._clearButton = new Button({
					label: this.clearButtonLabel,
					iconClass: 'umcIconDelete',
					callback: lang.hitch(this, function() {
						this.set('data', null);
					})
				});
				this.addChild(this._clearButton);
			}
		},

		postCreate: function() {
			this.inherited(arguments);

			// as soon as the user has selected a file, start the upload
			this._uploader.on('change', lang.hitch(this, function(data) {
				var allOk = array.every(data, function(ifile) {
					return ifile.size <= this.maxSize;
				}, this);
				if (!allOk) {
					dialog.alert(_('File cannot be uploaded, its maximum size may be %.1f MB.', this.maxSize / 1048576.0));
					this._uploader.reset();
				}
				else {
					when(this.canUpload(data[0]), lang.hitch(this, function(doUpload) {
						if (!doUpload) {
							// upload canceled
							this._uploader.reset();
							return;
						}

						// perform the upload
						var params = {};
						if (this.dynamicOptions) {
							if (typeof this.dynamicOptions == "function") {
								lang.mixin(params, this.dynamicOptions(params));
							}
							else if (typeof this.dynamicOptions == "object") {
								lang.mixin(params, this.dynamicOptions);
							}
						}
						// mixin the iframe information
						lang.mixin(params, {
							iframe: (this._uploader.uploadType === 'iframe') ? true : false
						});
						this._uploader.upload(params);
						this._updateLabel();
						this.onUploadStarted(data[0]);
					}));
				}
			}));

			// hook for showing the progress
			this._uploader.on('progress', lang.hitch(this, 'onProgress'));

			// notification as soon as the file has been uploaded
			this._uploader.on('complete', lang.hitch(this, function(data) {
				if (data && data.result instanceof Array) {
					this.set('data', data.result[0]);
					this.onUploaded(this.data);
				}
				else {
					this.set('data', null);
					var error = tools.parseError(data);
					if (200 !== error.status) {
						if (this.displayErrorMessage) {
							dialog.alert(error.message);
						}
						this.onError(error);
					} else {
						this.onUploaded(this.data);
					}
				}
				this._resetLabel();
			}));

			// setup events
			this._uploader.on('cancel', lang.hitch(this, '_resetLabel'));
			this._uploader.on('abort', lang.hitch(this, '_resetLabel'));
			this._uploader.on('error', lang.hitch(this, '_resetLabel'));

			// update the view
			this.set('value', this.value);
		},

		_setDataAttr: function(newVal) {
			this.data = newVal;
			this._settingData = true;
			this.set( 'value', newVal && 'content' in newVal ? newVal.content : '' );
			this._settingData = false;
		},

		_setValueAttr: function(newVal) {
			if (!this._settingData) {
				this.data = null;
			}
			this.value = newVal;

			if ( this.showClearButton ) {
				// decide whether to show/hide remove button
				domClass.toggle(this._clearButton.domNode, 'dijitHidden', !(typeof this.value == "string" && this.value !== ""));
			}

			// send events
			this.onChange(newVal);
			this.updateView(this.value, this.data);
		},

		_resetLabel: function() {
			if (!this._uploader) {
				return;
			}
			this.set('disabled', false);
			this.set('buttonLabel', this._origButtonLabel);
			this._uploader.reset();
		},

		_updateLabel: function() {
			if (!this.get('disabled')) {
				// make sure the button is disabled
				this.set('disabled', true);
			}
			this.set('buttonLabel', _('Uploading...'));
		},

		_setButtonLabelAttr: function(newVal) {
			if (!this._uploader) {
				return;
			}
			this.buttonLabel = newVal;
			this._uploader.set('label', newVal);
		},

		_setDisabledAttr: function(newVal) {
			if (!this._uploader || !this._uploader.inputNode) {
				return;
			}
			this._uploader.set('disabled', newVal);
			style.set(this._uploader.domNode, 'display', 'inline-block');
		},

		_getDisabledAttr: function() {
			return this._uploader.get('disabled');
		},

		canUpload: function(fileInfo) {
			// summary:
			//		Before uploading a file, this function is called to make sure
			//		that the given filename is valid. Return boolean or dojo/Deferred.
			// fileInfo: Object
			//		Info object for the requested file, contains properties 'name',
			//		'size', 'type'.
			return true;
		},

		onUploadStarted: function(fileInfo) {
			// event stub
		},

		onUploaded: function(data) {
			// event stub
		},

		onError: function(data) {
			// event stub
		},

		onProgress: function(data) {
			// event stub
		},

		onChange: function(data) {
			// event stub
		},

		updateView: function(value, data) {
			// summary:
			//		Custom view function that renders the file content that has been uploaded.
			//		The default is empty.
		}
	});
});


