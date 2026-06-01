    function apagar_conceito(designacao){
        $.ajax("/conceitos/" + designacao, {
            method: "DELETE",
            success: function(response){
                window.location.href ="/conceitos"
            },
            error: function(response){
                console.log(response)
            }
        })
    }

    	
new DataTable('#tabela_conceitos');