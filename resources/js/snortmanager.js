    var snortmanager = {}; // Global namespace
	
	$(document).ready(function() {

		$( "input:submit, a, button, input:reset", ".form").button();
		$( "button").button();
		
		$( ".clear",".form" ).focus(function(){
			$(this).val('');
		});

		$( "#active" ).button();
		
		$("#policy_object_list tbody").sortable( {
			placeholder : 'dropable'
		}).sortable('serialize');
		
		$('#policy_objects').submit(function() {
			$('#object_list','#policy_objects').val($('#policy_object_list tbody td').serialize());		
			return false;
			
		});
		
		$('input:text').button().css({
		'font' : 'inherit',
		'color' : 'inherit',
		'text-align' : 'left',
		'outline' : 'none',
        'cursor' : 'text'
		});
		
		$('tbody tr:odd', '#list').addClass('grey');
		
		$( "#dialog-confirm" ).data('did', 0);
		
		$( "#dialog-confirm" ).dialog({
			autoOpen: false,
			resizable: false,
			height:200,
			width: 500,
			modal: true,
			draggable : false,
			open : function() {
					var obj_id = $(this).data('did');
					$("#dialog-confirm #object-id").val(obj_id);
				},
			buttons: {
				Cancel: function() {
					$( this ).dialog( "close" );
				},
				"Delete": function() {
					$("#dialog-confirm #delete_object").submit();
				},
			}
		});
		
		$(".delete_object").click(function(){
			var the_id = $(this).attr("value");
			$("#dialog-confirm").data('did', the_id).dialog("open");
			return false
		});

		$( "#choose-object-dialog" ).dialog({
			autoOpen: false,
			height: 'auto',
			width: 'auto',
			modal: true,
			buttons: {
				Cancel: function() {
					$( this ).dialog( "close" );
				},
				Submit: function(){
					$("#choose-object").submit();
					$( this ).dialog( "close" );
				}
			},
			open: function(){

				var pol_id = $(this).data('oid');
				snortmanager.get_object(pol_id, $(this), false);
				$("#object-id","#choose-object").val();
				$("#policy-object", "#choose-object").val(pol_id);
				}
			});
		

		$( "#edit-object-dialog" ).dialog({
			autoOpen: false,
			height: 'auto',
			width: 'auto',
			modal: true,
			buttons: {
				Cancel: function() {
					$( this ).dialog( "close" );
				},
				Submit: function(){
					$("#edit-object").submit();
					$( this ).dialog( "close" );
				}
			},
			open: function(){

				var pol_id = $(this).data('oid');
				$("#policy-id", "#edit-object").val(pol_id);
				snortmanager.get_object(pol_id, $(this));
				}
			});
		
		$("#edit-object").submit(function(){
			var form_data = ($("#edit-object").serialize());
			$.ajax({
				type: "POST",
				url: '/policy/save/object/',
				data: form_data,
				error: function(){
					alert('Update failed');
				},
				success: function(){	
					location.reload();
				},
				complete: function(){
					//location.reload();
				}
			});
				
			return false;
		});
		
		$('#confirm_job_execution').dialog({
			autoOpen: false,
			height: 'auto',
			title: 'Confirm job execution',
			width: 'auto',
			buttons: {
				'No' : function(){
					$(this).dialog('close');
				},
				'Yes' : function(){
 					$.ajax({
						type: "POST",
						url: '/jobs/start_job/',
						data: $(this).data('job'),
						error: function(){
							$("#error_area").removeClass('hide_error');
							$("#error_text","#error_area").text('Error while starting job');
						},
						success: function(){
						},
						complete: function(){
							location.reload();
						}
					});
					$(this).dialog('close');
				}
			}
		});
		
		$('#delete_sensor').dialog({
			autoOpen: false,
			height: 'auto',
			title: 'Delete sensor',
			width: '400px',
			buttons: {
				'No' : function(){
					$(this).dialog('close');
				},
				'Yes' : function(){

					var sensor_id = $(this).data('sensor_id');
					snortmanager.post_data({'sensor_id' : sensor_id}, '/sensor/delete/');
					$(this).dialog('close');
				}
			}
		});
		
		
		$(".start_job").button().click(function(){
		    var job_to_start = $(this).val();
		    $('#confirm_job_execution').data('job', job_to_start).dialog("open");
		    return false;
		});
		
		$("#error_area").addClass('hide_error')
				
		$("#choose-object").submit(function(){
			var form_data = ($("#choose-object").serialize());
			$.ajax({
				type: "POST",
				url: '/policy/edit/choose_object/',
				data: form_data,
				error: function(){
					alert('Update failed');
				},
				success: function(){
					location.reload();
				},
				complete: function(){
					//location.reload();
				}
			});
				
			return false;
		});
		
		$("#select-object","#choose-object").change(function() {
			var object_id = $(this).val();
			snortmanager.get_single_object(object_id, "#choose-object");
			return false;
				
		});
	
	snortmanager.get_object = function(object_id, dialog) {
		
		$.getJSON('/policy/edit/policy_item/' + object_id + '/',function(data){
			$("#object-content", dialog).val(data.contents);
			$("#object-id", dialog).val(data.id);
			$("#object-type", dialog).val(data.type);
			$("#select-object",dialog).val(data.id); //CHEATING
			console.log(data);

		});
		return false;

	}
	
	snortmanager.show_systemlock = function(){
		$("#error_area").removeClass('hide_error');
		$("#error_text","#error_area").text('System lock is enabled!');
    	$("button, input:submit")
    	.addClass('disabled_button')
    	.attr("disabled",true);
    	
		return false;
	}
	
	snortmanager.post_data = function(form_data, url){
		$.ajax({
			type: "POST",
			url: url,
			data: form_data,
			error: function(){
				$("#error_area").removeClass('hide_error');
				$("#error_text","#error_area").text('Error while updating database!');
			},
			success: function(){
				location.reload();
			},
			});
				
			return false;
		};
	
	
	snortmanager.get_single_object = function(object_id, dialog) {
		$.getJSON('/policy/edit/get_object/' + object_id + '/', function(data){
			$("#policy-contents", dialog).val(data.contents);
			$("#object-id", dialog).val(data.id);
			$("#object-type", dialog).val(data.type);

		});
		return false;

	}
	
/*

*************** DIALOGS ***************

*/



	$("#delete_schedule").dialog({
		autoOpen: false,
		height: 'auto',
		width: 'auto',
		buttons: {
			Cancel : function(){
				$(this).dialog('close');
			},
			'OK' : function(){
				alert('You clicked OK, you dick!');
			},
		},
		
	});
	
	$("#add_new_location").dialog({
		autoOpen: false,
		height: 'auto',
		width: 'auto',
		title : 'Add location',
		buttons: {
			Cancel : function(){
				$(this).dialog('close');
			},
			'Create' : function(){
				$("#add_location_form", "#add_new_location").submit();
				$(this).dialog('close');
			},
		},
		
	});
	
		$("#add_location_form", "#add_new_location").submit(function(){
			var form_data = $("#add_location_form").serialize();
			var location_name = $("#location_name", "#add_location_form").val();
			$.ajax({
				type: "POST",
				url: '/sensor/location/add/',
				data: form_data,
				error: function(){
					alert('Update failed');
				},
				success: function(data){
				    $("#location_list")
				    .prepend($("<option></option>")
				    	.attr("value",data)
				    	.text(location_name)); 
				    	
				    $("#location_list").val(data);
				},
				complete: function(){
				}
			});
				
			return false;
		});
		
	$("#edit_sensor_form")
	.load("/sensor/addsensor/ #add_sensor")
	.dialog({
    	title: "Sensor administration",
		autoOpen: false,
		modal: true,
		height: 'auto',
		width: 'auto',
		open:  function(){
			$("tfoot", "#add_sensor").addClass('hide_error');

		    if (typeof $(this).data('loc') != 'undefined'){
			    
			    var loc = $(this).data('loc');
			    
			    $("#sensor_location", "#add_sensor").val(loc);
				
				$("#sensor_name", "#add_sensor").val('');
				$("#sensor_ip", "#add_sensor").val('');
				$("#sensor_description", "#add_sensor").val('');
				$("#sensor_id", "#add_sensor").val(0);
			}
			
			if (typeof $(this).data('sensor') != 'undefined') {
				var sensor = $(this).data('sensor');
				
				$.getJSON('/sensor/get/sensor/' + sensor + '/', function(data){
				$("#sensor_name").val(data.name);
				$("#sensor_location").val(data.location);
				$("#sensor_ip").val(data.ip);
				$("#sensor_description").val(data.description);
				$("#sensor_id").val(data.id);
				});
			} 
		},
		
		buttons: {
			'Cancel' : function(){
				$(this).dialog('close');
			},
			'Save' : function(){
			    var form_data = $("#add_sensor").serialize();
			    
			    snortmanager.post_data(form_data, '/sensor/save/');
			    $(this).dialog('close');
			},
		},
	});

/*
***************	BUTTONS ***************

*/
		$( ".delete_sensor").button()
		.click(function(){
			var sensor_id = $(this).val()
			$("#delete_sensor").data('sensor_id', sensor_id).dialog("open");
		});

		$(".new_location").button().click(function() {
				$("#add_new_location").dialog('open');
				return false;
				
		});

		$( ".delete_schedule").button()
		.click(function(){
			$("#delete_schedule").dialog("open");
		});
		
		$( ".edit_object" )
			.button()
			.click(function() {
				var the_id = $(this).attr("value");
				$( "#edit-object-dialog" ).data('oid', the_id).dialog( "open" );
				return false;
			});

		$( ".choose_object" )
			.button()
			.click(function() {
				var the_id = $(this).attr("value");
				$( "#choose-object-dialog" ).data('oid', the_id).dialog( "open" );
				return false;
			});
	
	$(".new_sensor").button()
	.click(function(){
    	var loc = $(this).val(); // Location
    	if (loc == 0) {
    		loc = $("#location_list").val();
    	}
			$("#edit_sensor_form").data('loc', loc).dialog("open");
		return false;
	});	
	
	$(".edit_sensor").button()
	.click(function(){
		var sensor = $(this).val();
		$("#edit_sensor_form").data('sensor', sensor).dialog("open");
		return false;
	});
	
// EOF
});

	

